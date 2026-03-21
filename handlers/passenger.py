from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from db import queries
from keyboards.keyboards import (
    share_location_kb, passengers_count_kb, cancel_kb,
    main_menu_kb, passenger_confirm_kb,
)
from utils.templates import passenger_announcement_text
from config import CHANNEL_ID

router = Router()


class PassengerForm(StatesGroup):
    waiting_location = State()
    waiting_count = State()
    waiting_price = State()
    waiting_note = State()


DIRECTION_MAP = {
    "🚌 Nukus ➡️ Mangit": "nukus_mangit",
    "🚌 Mangit ➡️ Nukus": "mangit_nukus",
}


# StateFilter(None) — faqat hech qanday state bo'lmaganda ishlaydi
# Bu haydovchining waiting_direction state ini o'g'irlamaydi
@router.message(StateFilter(None), F.text.in_(["🚌 Nukus ➡️ Mangit", "🚌 Mangit ➡️ Nukus"]))
async def start_passenger_flow(message: Message, state: FSMContext, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return

    if user.is_banned:
        await message.answer("🚫 Siz bloklangansiz. Admin bilan bog'laning.")
        return

    if user.role == "driver":
        await message.answer(
            "🚗 Siz haydovchi sifatida ro'yxatdansiz.\n"
            "Yo'lovchi sifatida e'lon berish uchun rolni o'zgartiring:",
            reply_markup=main_menu_kb("driver"),
        )
        return

    existing = await queries.get_active_announcement_by_user(session, message.from_user.id)
    if existing:
        from keyboards.keyboards import active_ann_kb
        await message.answer(
            "⚠️ Sizda allaqachon faol e'lon mavjud.\n"
            "Yangi e'lon berish uchun avvalgi e'lonni yakunlang yoki bekor qiling:",
            reply_markup=active_ann_kb(existing.id, "passenger"),
        )
        return

    direction = DIRECTION_MAP[message.text]
    await state.update_data(direction=direction)
    await state.set_state(PassengerForm.waiting_location)

    await message.answer(
        "📍 Joylashuvingizni yuboring yoki o'tkazib yuboring:",
        reply_markup=share_location_kb(),
    )


@router.message(PassengerForm.waiting_location, F.location)
async def got_location(message: Message, state: FSMContext):
    await state.update_data(
        location_lat=message.location.latitude,
        location_lon=message.location.longitude,
    )
    await state.set_state(PassengerForm.waiting_count)
    await message.answer(
        "👥 Necha kishi? (o'zingiz bilan birga):",
        reply_markup=passengers_count_kb(),
    )


@router.message(PassengerForm.waiting_location, F.text == "⏭️ O'tkazib yuborish")
async def skip_location(message: Message, state: FSMContext):
    await state.update_data(location_lat=None, location_lon=None)
    await state.set_state(PassengerForm.waiting_count)
    await message.answer(
        "👥 Necha kishi? (o'zingiz bilan birga):",
        reply_markup=passengers_count_kb(),
    )


@router.callback_query(F.data.startswith("pcount_"), PassengerForm.waiting_count)
async def got_count(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.split("_")[1])
    await state.update_data(passengers_count=count)
    await state.set_state(PassengerForm.waiting_price)
    await callback.message.edit_text(f"✅ {count} kishi tanlandi.")
    await callback.message.answer(
        "💰 Taklif narxingizni yozing (masalan: 25000 so'm):",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(PassengerForm.waiting_price)
async def got_price(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        user = await queries.get_user(session, message.from_user.id)
        role = user.role if user else None
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(role))
        return

    await state.update_data(price=message.text)
    await state.set_state(PassengerForm.waiting_note)
    await message.answer(
        "📝 Izoh qo'shing (ixtiyoriy). Masalan: 'Mushugim bor', 'Yukim ko'p'\n"
        "Yo'q bo'lsa /skip yozing:",
        reply_markup=cancel_kb(),
    )


@router.message(PassengerForm.waiting_note)
async def got_note(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        user = await queries.get_user(session, message.from_user.id)
        role = user.role if user else None
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(role))
        return

    note = None if message.text == "/skip" else message.text
    data = await state.get_data()
    await state.clear()

    ann = await queries.create_announcement(
        session,
        user_id=message.from_user.id,
        direction=data["direction"],
        passengers_count=data["passengers_count"],
        price=data["price"],
        note=note,
        location_lat=data.get("location_lat"),
        location_lon=data.get("location_lon"),
    )

    user = await queries.get_user(session, message.from_user.id)
    await queries.update_user_role(session, user.user_id, "passenger")

    text = passenger_announcement_text(ann, user)
    channel_msg = await bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    await queries.update_announcement_channel_msg(session, ann.id, channel_msg.message_id)

    await message.answer(
        "✅ E'loningiz kanalga joylandi!\n"
        "30 daqiqadan keyin sizdan so'rov yuboriladi.",
        reply_markup=main_menu_kb("passenger"),
    )


@router.callback_query(F.data.startswith("p_done_"))
async def passenger_done(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    ann_id = int(callback.data.split("_")[2])
    ann = await queries.get_announcement(session, ann_id)
    if not ann:
        await callback.answer("E'lon topilmadi.")
        return

    if ann.channel_msg_id:
        try:
            await bot.delete_message(CHANNEL_ID, ann.channel_msg_id)
        except Exception:
            pass

    await queries.update_announcement_status(session, ann_id, "completed")
    await callback.message.edit_text("✅ E'lon yakunlandi va kanaldan o'chirildi.")
    await callback.answer()


@router.callback_query(F.data.startswith("p_reload_"))
async def passenger_reload(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    ann_id = int(callback.data.split("_")[2])
    ann = await queries.get_announcement(session, ann_id)
    if not ann:
        await callback.answer("E'lon topilmadi.")
        return

    if ann.channel_msg_id:
        try:
            await bot.delete_message(CHANNEL_ID, ann.channel_msg_id)
        except Exception:
            pass

    user = await queries.get_user(session, ann.user_id)
    text = passenger_announcement_text(ann, user)
    ann.created_at = datetime.utcnow()
    await session.commit()

    channel_msg = await bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    await queries.update_announcement_channel_msg(session, ann_id, channel_msg.message_id)
    await callback.message.edit_text("🔄 E'lon yangilandi va kanal oxiriga joylashdi.")
    await callback.answer()