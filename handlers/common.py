from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from db import queries
from keyboards.keyboards import (
    share_contact_kb, main_menu_kb, rating_kb,
    role_select_kb, profile_edit_kb, cancel_kb,
)

router = Router()

DIRECTION_LABELS = {
    "nukus_mangit": "Nukus ➡️ Mangit",
    "mangit_nukus": "Mangit ➡️ Nukus",
}
STATUS_LABELS = {
    "active": "🟢 Faol",
    "completed": "✅ Yakunlangan",
    "expired": "⏰ Muddati o'tgan",
}


class RegForm(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_role = State()


class RoleChangeForm(StatesGroup):
    waiting_role = State()


class ProfileEditForm(StatesGroup):
    waiting_new_name = State()
    waiting_new_phone = State()


class ComplaintForm(StatesGroup):
    waiting_text = State()


# ============ START ============

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    user = await queries.get_user(session, message.from_user.id)

    if user:
        if user.is_banned:
            await message.answer("🚫 Siz bloklangansiz. Admin bilan bog'laning.")
            return

        role = await queries.get_admin_role(session, user.user_id)
        if role == "super_admin":
            from keyboards.keyboards import super_admin_kb
            await message.answer(
                f"👑 Xush kelibsiz, Super Admin {user.full_name}!\nPanel:",
                reply_markup=super_admin_kb(),
            )
        elif role == "admin":
            from keyboards.keyboards import admin_kb
            await message.answer(
                f"👮 Xush kelibsiz, Admin {user.full_name}!\nPanel:",
                reply_markup=admin_kb(),
            )
        else:
            await message.answer(
                f"👋 Xush kelibsiz, {user.full_name}!\nQayerga borishni tanlang:",
                reply_markup=main_menu_kb(user.role),
            )
    else:
        welcome = await queries.get_setting(
            session, "welcome_message",
            "Nukus-Mangit Taksi Hamrohi botiga xush kelibsiz!"
        )
        await state.set_state(RegForm.waiting_name)
        await message.answer(f"👋 Assalomu alaykum! {welcome}\n\nRo'yxatdan o'tish uchun ismingizni yuboring:")


@router.message(RegForm.waiting_name)
async def got_name(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 2:
        await message.answer("Iltimos, to'g'ri ism kiriting.")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(RegForm.waiting_phone)
    await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=share_contact_kb())


@router.message(RegForm.waiting_phone, F.contact)
async def got_phone(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    user = await queries.create_user(session, message.from_user.id, data["full_name"])
    await queries.update_user_phone(session, user.user_id, phone)
    await queries.add_log(session, user.user_id, "register", f"Yangi foydalanuvchi: {data['full_name']}")
    await state.update_data(user_created=True)
    await state.set_state(RegForm.waiting_role)
    await message.answer("✅ Zo'r! Siz odatda kim bo'lasiz?", reply_markup=role_select_kb())


@router.message(RegForm.waiting_phone)
async def phone_not_shared(message: Message):
    await message.answer("Iltimos, tugma orqali telefon raqamingizni yuboring.", reply_markup=share_contact_kb())


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
    await message.answer("Yangi rolingizni tanlang:", reply_markup=role_select_kb())


@router.message(RoleChangeForm.waiting_role, F.text.in_(["🙋 Yo'lovchi", "🚗 Haydovchi"]))
async def change_role_done(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    role = "driver" if message.text == "🚗 Haydovchi" else "passenger"
    await queries.update_user_role(session, message.from_user.id, role)
    await queries.add_log(session, message.from_user.id, "role_change", role)
    role_label = "Haydovchi 🚗" if role == "driver" else "Yo'lovchi 🙋"
    await message.answer(f"✅ Rolingiz o'zgartirildi: {role_label}", reply_markup=main_menu_kb(role))


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

    admin_role = await queries.get_admin_role(session, user.user_id)
    admin_text = ""
    if admin_role == "super_admin":
        admin_text = "\n👑 Super Admin"
    elif admin_role == "admin":
        admin_text = "\n👮 Admin"

    await message.answer(
        f"👤 <b>Ma'lumotlarim</b>\n\n"
        f"Ism: {user.full_name}\n"
        f"Tel: {user.phone}\n"
        f"Rol: {role_label}{rating_text}{admin_text}\n"
        f"Ro'yxat: {user.created_at.strftime('%d.%m.%Y')}",
        parse_mode="HTML",
        reply_markup=profile_edit_kb(),
    )


# ============ PROFIL TAHRIRLASH ============

@router.callback_query(F.data == "profile_edit_name")
async def profile_edit_name_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditForm.waiting_new_name)
    await callback.message.answer("✏️ Yangi ismingizni kiriting:", reply_markup=cancel_kb())
    await callback.answer()


@router.message(ProfileEditForm.waiting_new_name)
async def profile_edit_name_done(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        user = await queries.get_user(session, message.from_user.id)
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(user.role if user else None))
        return
    if not message.text or len(message.text) < 2:
        await message.answer("Iltimos, to'g'ri ism kiriting.")
        return
    await queries.update_user_name(session, message.from_user.id, message.text.strip())
    await queries.add_log(session, message.from_user.id, "profile_name_edit", message.text.strip())
    await state.clear()
    user = await queries.get_user(session, message.from_user.id)
    await message.answer("✅ Ismingiz yangilandi.", reply_markup=main_menu_kb(user.role if user else None))


@router.callback_query(F.data == "profile_edit_phone")
async def profile_edit_phone_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ProfileEditForm.waiting_new_phone)
    await callback.message.answer("📱 Yangi telefon raqamingizni yuboring:", reply_markup=share_contact_kb())
    await callback.answer()


@router.message(ProfileEditForm.waiting_new_phone, F.contact)
async def profile_edit_phone_done(message: Message, state: FSMContext, session: AsyncSession):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await queries.update_user_phone(session, message.from_user.id, phone)
    await queries.add_log(session, message.from_user.id, "profile_phone_edit", phone)
    await state.clear()
    user = await queries.get_user(session, message.from_user.id)
    await message.answer("✅ Telefon raqamingiz yangilandi.", reply_markup=main_menu_kb(user.role if user else None))


# ============ E'LON TARIXI ============

@router.message(F.text == "📜 E'lonlarim")
async def my_announcements(message: Message, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return

    anns = await queries.get_user_announcements(session, message.from_user.id, limit=10)
    if not anns:
        await message.answer("Sizda hali e'lon yo'q.")
        return

    text = "📜 <b>E'lonlarim (oxirgi 10):</b>\n\n"
    for ann in anns:
        direction = DIRECTION_LABELS.get(ann.direction, ann.direction)
        status = STATUS_LABELS.get(ann.status, ann.status)
        text += (
            f"#{ann.id} — {direction}\n"
            f"   {status} | {ann.price} | {ann.created_at.strftime('%d.%m %H:%M')}\n\n"
        )
    await message.answer(text, parse_mode="HTML")


# ============ SHIKOYAT ============

@router.callback_query(F.data.startswith("complaint_"))
async def start_complaint(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if callback.data.startswith("complaint_close_") or callback.data.startswith("complaint_ban_"):
        return
    parts = callback.data.split("_")
    against_id = int(parts[1])
    ann_id = int(parts[2]) if len(parts) > 2 and parts[2] != "0" else None

    user = await queries.get_user(session, callback.from_user.id)
    if not user:
        await callback.answer("Avval ro'yxatdan o'ting.", show_alert=True)
        return

    await state.update_data(complaint_against=against_id, complaint_ann=ann_id)
    await state.set_state(ComplaintForm.waiting_text)
    await callback.message.answer(
        "📝 Shikoyat matnini yuboring (nima sodir bo'ldi?):",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(ComplaintForm.waiting_text)
async def submit_complaint(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        user = await queries.get_user(session, message.from_user.id)
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb(user.role if user else None))
        return

    data = await state.get_data()
    await state.clear()

    complaint = await queries.create_complaint(
        session,
        from_user_id=message.from_user.id,
        against_user_id=data["complaint_against"],
        text=message.text,
        ann_id=data.get("complaint_ann"),
    )
    await queries.add_log(session, message.from_user.id, "complaint_submitted", f"Against: {data['complaint_against']}")

    # Adminlarga xabarnoma
    admins = await queries.get_all_admins(session)
    from keyboards.keyboards import complaint_review_kb
    for admin in admins:
        try:
            await bot.send_message(
                admin.user_id,
                f"🚨 <b>Yangi shikoyat #{complaint.id}</b>\n\n"
                f"Kim: <code>{message.from_user.id}</code>\n"
                f"Kimga: <code>{data['complaint_against']}</code>\n"
                f"Matn: {message.text[:300]}",
                parse_mode="HTML",
                reply_markup=complaint_review_kb(complaint.id),
            )
        except Exception:
            pass

    user = await queries.get_user(session, message.from_user.id)
    await message.answer(
        "✅ Shikoyatingiz qabul qilindi. Admin tez orada ko'rib chiqadi.",
        reply_markup=main_menu_kb(user.role if user else None),
    )


# ============ REYTING ============

@router.callback_query(F.data.startswith("rate_"))
async def give_rating(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split("_")
    driver_id = int(parts[1])
    score = int(parts[2])

    await queries.add_rating(session, driver_id=driver_id, passenger_id=callback.from_user.id, score=score)
    await queries.add_log(session, callback.from_user.id, "rating_given", f"Driver: {driver_id}, score: {score}")

    stars = "⭐" * score
    await callback.message.edit_text(f"✅ Rahmat! Siz {stars} qo'ydingiz.")
    await callback.answer("Baholaganingiz uchun rahmat!")


# ============ BEKOR QILISH ============

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
    await queries.add_log(session, callback.from_user.id, "ann_cancelled", f"ann_id: {ann_id}")
    await callback.message.edit_text("✅ E'lon bekor qilindi.")
    await callback.answer()
