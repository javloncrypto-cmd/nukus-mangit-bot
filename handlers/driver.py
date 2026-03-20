from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from db import queries
from keyboards.keyboards import (
    cancel_kb, main_menu_kb, driver_control_kb,
    driver_seats_kb, passengers_count_kb,
)
from utils.templates import driver_announcement_text
from config import CHANNEL_ID

router = Router()


class DriverForm(StatesGroup):
    waiting_direction = State()
    waiting_seats = State()
    waiting_price = State()
    waiting_note = State()
    waiting_edit_text = State()


DIRECTION_MAP = {
    "🚌 Nukus ➡️ Mangit": "nukus_mangit",
    "🚌 Mangit ➡️ Nukus": "mangit_nukus",
}


@router.message(F.text == "🚗 Haydovchi e'loni")
async def start_driver_flow(message: Message, state: FSMContext, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user or user.is_banned:
        await message.answer("🚫 Siz bloklangansiz.")
        return

    existing = await queries.get_active_announcement_by_user(session, message.from_user.id)
    if existing:
        await message.answer("⚠️ Sizda allaqachon faol e'lon bor. Avval uni yakunlang.")
        return

    await state.set_state(DriverForm.waiting_direction)
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚌 Nukus ➡️ Mangit"), KeyboardButton(text="🚌 Mangit ➡️ Nukus")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
    )
    await message.answer("Yo'nalishni tanlang:", reply_markup=kb)


@router.message(DriverForm.waiting_direction)
async def driver_direction(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb("driver"))
        return
    if message.text not in DIRECTION_MAP:
        await message.answer("Iltimos tugmadan tanlang.")
        return
    await state.update_data(direction=DIRECTION_MAP[message.text])
    await state.set_state(DriverForm.waiting_seats)
    await message.answer("👥 Bo'sh joylar sonini tanlang:", reply_markup=passengers_count_kb())


@router.callback_query(F.data.startswith("pcount_"), DriverForm.waiting_seats)
async def driver_seats(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.split("_")[1])
    await state.update_data(seats=count)
    await state.set_state(DriverForm.waiting_price)
    await callback.message.edit_text(f"✅ {count} joy tanlandi.")
    await callback.message.answer("💰 Narxni yozing:", reply_markup=cancel_kb())
    await callback.answer()


@router.message(DriverForm.waiting_price)
async def driver_price(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb("driver"))
        return
    await state.update_data(price=message.text)
    await state.set_state(DriverForm.waiting_note)
    await message.answer("📝 Izoh (ixtiyoriy, yo'q bo'lsa /skip):", reply_markup=cancel_kb())


@router.message(DriverForm.waiting_note)
async def driver_note(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb("driver"))
        return

    note = None if message.text == "/skip" else message.text
    data = await state.get_data()
    await state.clear()

    ann = await queries.create_announcement(
        session,
        user_id=message.from_user.id,
        direction=data["direction"],
        passengers_count=data["seats"],
        price=data["price"],
        note=note,
    )

    user = await queries.get_user(session, message.from_user.id)
    await queries.update_user_role(session, user.user_id, "driver")

    text = driver_announcement_text(ann, user)
    channel_msg = await bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    await queries.update_announcement_channel_msg(session, ann.id, channel_msg.message_id)

    await message.answer(
        "✅ E'loningiz kanalga joylandi!\n"
        "1 daqiqadan keyin yo'lovchi topilganmi deb so'rayman.",
        reply_markup=main_menu_kb("driver"),
    )

    # Schedule 1-minute interval check via bot data
    bot_data = bot.__dict__.get("_bot_data", {})
    pending = bot_data.get("driver_pending", [])
    pending.append({"ann_id": ann.id, "user_id": message.from_user.id})
    if "_bot_data" not in bot.__dict__:
        bot._bot_data = {}
    bot._bot_data["driver_pending"] = pending


# ============ DRIVER CONTROL CALLBACKS ============

@router.callback_query(F.data.startswith("d_reload_"))
async def driver_reload(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    ann_id = int(callback.data.split("_")[2])
    ann = await queries.get_announcement(session, ann_id)
    if not ann or ann.user_id != callback.from_user.id:
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    if ann.channel_msg_id:
        try:
            await bot.delete_message(CHANNEL_ID, ann.channel_msg_id)
        except Exception:
            pass

    ann.created_at = datetime.utcnow()
    await session.commit()

    user = await queries.get_user(session, ann.user_id)
    text = driver_announcement_text(ann, user)
    channel_msg = await bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    await queries.update_announcement_channel_msg(session, ann_id, channel_msg.message_id)

    await callback.message.edit_text(
        "🔄 E'lon yangilandi.",
        reply_markup=driver_control_kb(ann_id),
    )
    await callback.answer("E'lon qayta yuklandi!")


@router.callback_query(F.data.startswith("d_change_"))
async def driver_change_seats(callback: CallbackQuery, session: AsyncSession):
    ann_id = int(callback.data.split("_")[2])
    await callback.message.answer(
        "Yangi bo'sh joylar sonini tanlang:",
        reply_markup=driver_seats_kb(ann_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("d_seats_"))
async def driver_seats_changed(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    parts = callback.data.split("_")
    ann_id = int(parts[2])
    new_count = int(parts[3])

    ann = await queries.get_announcement(session, ann_id)
    if not ann:
        await callback.answer("E'lon topilmadi.")
        return

    await queries.update_announcement_passengers(session, ann_id, new_count)
    ann.passengers_count = new_count

    if ann.channel_msg_id:
        user = await queries.get_user(session, ann.user_id)
        text = driver_announcement_text(ann, user)
        try:
            await bot.edit_message_text(text, CHANNEL_ID, ann.channel_msg_id, parse_mode="HTML")
        except Exception:
            pass

    await callback.message.edit_text(f"✅ Bo'sh joylar {new_count} taga o'zgartirildi.")
    await callback.answer()


@router.callback_query(F.data.startswith("d_edit_"))
async def driver_edit_start(callback: CallbackQuery, state: FSMContext):
    ann_id = int(callback.data.split("_")[2])
    await state.update_data(edit_ann_id=ann_id)
    await state.set_state(DriverForm.waiting_edit_text)
    await callback.message.answer("✍️ Yangi e'lon matnini yuboring (narx yoki izoh):", reply_markup=cancel_kb())
    await callback.answer()


@router.message(DriverForm.waiting_edit_text)
async def driver_edit_done(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb("driver"))
        return

    data = await state.get_data()
    ann_id = data["edit_ann_id"]
    await state.clear()

    ann = await queries.get_announcement(session, ann_id)
    if not ann:
        await message.answer("E'lon topilmadi.")
        return

    # Update note field with new text
    ann.note = message.text
    await session.commit()

    if ann.channel_msg_id:
        user = await queries.get_user(session, ann.user_id)
        text = driver_announcement_text(ann, user)
        try:
            await bot.edit_message_text(text, CHANNEL_ID, ann.channel_msg_id, parse_mode="HTML")
        except Exception:
            pass

    await message.answer("✅ E'lon yangilandi.", reply_markup=main_menu_kb("driver"))


@router.callback_query(F.data.startswith("d_full_"))
async def driver_full(callback: CallbackQuery, session: AsyncSession, bot: Bot):
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
    await callback.message.edit_text("✅ E'lon yakunlandi! 1 soatdan keyin safar haqida so'rayman.")
    await callback.answer()


@router.callback_query(F.data.startswith("d_found_"))
async def driver_passenger_found(callback: CallbackQuery):
    await callback.message.edit_text("✅ Zo'r! Xavsiz yo'l tilaymiz! 🚗")
    await callback.answer()


@router.callback_query(F.data.startswith("d_notfound_"))
async def driver_passenger_notfound(callback: CallbackQuery, session: AsyncSession):
    ann_id = int(callback.data.split("_")[2])
    ann = await queries.get_announcement(session, ann_id)
    await callback.message.edit_text(
        "Tushunarli. E'lon hali ham kanalda turibdi.",
        reply_markup=driver_control_kb(ann_id) if ann else None,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("d_trip_done_"))
async def driver_trip_done(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    ann_id = int(callback.data.split("_")[3])
    # Send rating request to passengers (simplified: send to driver's chat for now)
    await callback.message.edit_text(
        "✅ Ajoyib! Yo'lovchilar tez orada baholash so'rovi oladi."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("d_trip_cancel_"))
async def driver_trip_cancel(callback: CallbackQuery):
    await callback.message.edit_text("Tushunarli. Keyinroq yana so'rayman.")
    await callback.answer()
