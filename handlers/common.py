from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from db import queries
from keyboards.keyboards import share_contact_kb, main_menu_kb, rating_kb, role_select_kb
from config import ADMIN_IDS

router = Router()


class RegForm(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_role = State()


class RoleChangeForm(StatesGroup):
    waiting_role = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await queries.get_user(session, message.from_user.id)

    if user:
        if user.is_banned:
            await message.answer("🚫 Siz bloklangansiz. Admin bilan bog'laning.")
            return
        await message.answer(
            f"👋 Xush kelibsiz, {user.full_name}!\nQayerga borishni tanlang:",
            reply_markup=main_menu_kb(user.role),
        )
    else:
        await state.set_state(RegForm.waiting_name)
        await message.answer(
            "👋 Assalomu alaykum! Nukus-Mangit Taksi Hamrohi botiga xush kelibsiz!\n\n"
            "Ro'yxatdan o'tish uchun ismingizni yuboring:"
        )


@router.message(RegForm.waiting_name)
async def got_name(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 2:
        await message.answer("Iltimos, to'g'ri ism kiriting.")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(RegForm.waiting_phone)
    await message.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=share_contact_kb(),
    )


@router.message(RegForm.waiting_phone, F.contact)
async def got_phone(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    user = await queries.create_user(session, message.from_user.id, data["full_name"])
    await queries.update_user_phone(session, user.user_id, phone)
    await state.update_data(user_created=True)
    await state.set_state(RegForm.waiting_role)

    await message.answer(
        "✅ Zo'r! Endi o'zingiz haqida ayting:\nSiz odatda kim bo'lasiz?",
        reply_markup=role_select_kb(),
    )


@router.message(RegForm.waiting_phone)
async def phone_not_shared(message: Message):
    await message.answer(
        "Iltimos, tugma orqali telefon raqamingizni yuboring.",
        reply_markup=share_contact_kb(),
    )


@router.message(RegForm.waiting_role, F.text.in_(["🙋 Yo'lovchi", "🚗 Haydovchi"]))
async def got_role(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    role = "driver" if message.text == "🚗 Haydovchi" else "passenger"
    await queries.update_user_role(session, message.from_user.id, role)

    role_label = "Haydovchi 🚗" if role == "driver" else "Yo'lovchi 🙋"
    await message.answer(
        f"✅ Ro'yxatdan o'tdingiz!\nRolingiz: {role_label}\n\nMenyu:",
        reply_markup=main_menu_kb(role),
    )


# ============ ROL O'ZGARTIRISH ============

@router.message(F.text == "🔄 Rolni o'zgartirish")
async def change_role_start(message: Message, state: FSMContext):
    await state.set_state(RoleChangeForm.waiting_role)
    await message.answer(
        "Yangi rolingizni tanlang:",
        reply_markup=role_select_kb(),
    )


@router.message(RoleChangeForm.waiting_role, F.text.in_(["🙋 Yo'lovchi", "🚗 Haydovchi"]))
async def change_role_done(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    role = "driver" if message.text == "🚗 Haydovchi" else "passenger"
    await queries.update_user_role(session, message.from_user.id, role)
    role_label = "Haydovchi 🚗" if role == "driver" else "Yo'lovchi 🙋"
    await message.answer(
        f"✅ Rolingiz o'zgartirildi: {role_label}",
        reply_markup=main_menu_kb(role),
    )


# ============ MA'LUMOTIM ============

@router.message(F.text == "ℹ️ Ma'lumotim")
async def my_info(message: Message, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return

    role_label = {"passenger": "Yo'lovchi 🙋", "driver": "Haydovchi 🚗"}.get(user.role or "", "Belgilanmagan")
    avg = await queries.get_driver_avg_rating(session, user.user_id)
    rating_text = f"\n⭐ Reytingim: {avg:.1f}" if avg else ""
    admin_text = "\n👑 Admin" if is_admin(user.user_id) else ""

    await message.answer(
        f"👤 <b>Ma'lumotlarim</b>\n\n"
        f"Ism: {user.full_name}\n"
        f"Tel: {user.phone}\n"
        f"Rol: {role_label}{rating_text}{admin_text}\n"
        f"Ro'yxat: {user.created_at.strftime('%d.%m.%Y')}",
        parse_mode="HTML",
    )


# ============ REYTING ============

@router.callback_query(F.data.startswith("rate_"))
async def give_rating(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split("_")
    driver_id = int(parts[1])
    score = int(parts[2])

    await queries.add_rating(
        session,
        driver_id=driver_id,
        passenger_id=callback.from_user.id,
        score=score,
    )

    stars = "⭐" * score
    await callback.message.edit_text(f"✅ Rahmat! Siz {stars} qo'ydingiz.")
    await callback.answer("Baholaganingiz uchun rahmat!")


@router.message(Command("cancel"))
async def cancel_any(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await queries.get_user(session, message.from_user.id)
    role = user.role if user else None
    await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(role))


# ============ E'LON BEKOR QILISH ============

@router.callback_query(F.data.startswith("cancel_ann_"))
async def cancel_announcement(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    from config import CHANNEL_ID
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

    await queries.update_announcement_status(session, ann_id, "completed")
    await callback.message.edit_text("✅ E'lon bekor qilindi. Endi yangi e'lon bera olasiz.")
    await callback.answer()
