from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db import queries
from db.database import Complaint
from keyboards.keyboards import admin_kb, main_menu_kb, complaint_review_kb

router = Router()


class AdminForm(StatesGroup):
    waiting_ban_id = State()
    waiting_unban_id = State()


async def check_admin(session: AsyncSession, user_id: int) -> bool:
    return await queries.is_admin_or_super(session, user_id)


# ============ PANEL ============

@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    role = await queries.get_admin_role(session, message.from_user.id)
    if role == "super_admin":
        from keyboards.keyboards import super_admin_kb
        await message.answer("👑 Super Admin panel:", reply_markup=super_admin_kb())
    else:
        await message.answer("👮 Admin panel:", reply_markup=admin_kb())


# ============ STATISTIKA ============

@router.message(F.text == "📊 Statistika")
async def stats(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    total_users = await queries.get_all_users_count(session)
    today_anns = await queries.get_today_announcements_count(session)
    direction_stats = await queries.get_direction_stats(session)
    admins = await queries.get_all_admins(session)

    admin_text = ""
    for a in admins:
        icon = "👑" if a.role == "super_admin" else "👮"
        name = a.user.full_name if a.user else str(a.user_id)
        admin_text += f"  {icon} {name}\n"

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👤 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"📢 Bugungi e'lonlar: <b>{today_anns}</b>\n\n"
        f"📍 Faol e'lonlar:\n"
        f"  • Nukus→Mangit: <b>{direction_stats['nukus_mangit']}</b>\n"
        f"  • Mangit→Nukus: <b>{direction_stats['mangit_nukus']}</b>\n\n"
        f"👥 Adminlar:\n{admin_text or '  —'}"
    )
    await message.answer(text, parse_mode="HTML")


# ============ FAOL E'LONLAR ============

@router.message(F.text == "📢 Faol e'lonlar")
async def all_active_announcements(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    anns = await queries.get_all_active_announcements(session)
    if not anns:
        await message.answer("Hozircha faol e'lon yo'q.")
        return

    text = f"📢 <b>Faol e'lonlar: {len(anns)} ta</b>\n\n"
    for ann in anns[:20]:
        direction = "N→M" if ann.direction == "nukus_mangit" else "M→N"
        name = ann.user.full_name if ann.user else "?"
        text += (
            f"#{ann.id} [{direction}] {name} — {ann.price}\n"
            f"   {ann.passengers_count} kishi | {ann.created_at.strftime('%d.%m %H:%M')}\n\n"
        )

    await message.answer(text[:4000], parse_mode="HTML")


# ============ QORA RO'YXAT ============

@router.message(F.text == "🚫 Qora ro'yxat")
async def blacklist(message: Message, session: AsyncSession, state: FSMContext):
    if not await check_admin(session, message.from_user.id):
        return

    await state.set_state(AdminForm.waiting_ban_id)
    await message.answer(
        "Bloklash uchun foydalanuvchi ID sini yuboring\n(/cancel — bekor qilish):"
    )


@router.message(AdminForm.waiting_ban_id)
async def ban_user_action(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_kb())
        return
    try:
        user_id = int(message.text.strip())
        user = await queries.get_user(session, user_id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi. ID ni tekshiring.")
            return
        await queries.ban_user(session, user_id, True)
        await queries.add_log(session, message.from_user.id, "user_banned", f"target: {user_id}")
        await state.clear()
        await message.answer(
            f"✅ {user.full_name} (<code>{user_id}</code>) bloklandi.",
            parse_mode="HTML",
            reply_markup=admin_kb(),
        )
    except ValueError:
        await message.answer("Noto'g'ri ID. Faqat raqam kiriting.")


# ============ BLOK OCHISH ============

@router.message(F.text == "🔓 Blok ochish")
async def unban_start(message: Message, state: FSMContext, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return
    await state.set_state(AdminForm.waiting_unban_id)
    await message.answer("Blokni ochish uchun foydalanuvchi ID sini yuboring:")


@router.message(AdminForm.waiting_unban_id)
async def unban_user_action(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_kb())
        return
    try:
        user_id = int(message.text.strip())
        user = await queries.get_user(session, user_id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return
        await queries.ban_user(session, user_id, False)
        await queries.add_log(session, message.from_user.id, "user_unbanned", f"target: {user_id}")
        await state.clear()
        await message.answer(
            f"✅ {user.full_name} (<code>{user_id}</code>) blokdan chiqarildi.",
            parse_mode="HTML",
            reply_markup=admin_kb(),
        )
    except ValueError:
        await message.answer("Noto'g'ri ID.")


# ============ SHIKOYATLAR ============

@router.message(F.text == "📋 Shikoyatlar")
async def complaints(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    open_complaints = await queries.get_open_complaints(session)
    if not open_complaints:
        await message.answer("Hozircha ko'rib chiqilmagan shikoyat yo'q.")
        return

    for c in open_complaints[:10]:
        from_user = await queries.get_user(session, c.from_user_id)
        against_user = await queries.get_user(session, c.against_user_id)
        from_name = from_user.full_name if from_user else str(c.from_user_id)
        against_name = against_user.full_name if against_user else str(c.against_user_id)
        text = (
            f"📋 <b>Shikoyat #{c.id}</b>\n"
            f"Kimdan: {from_name} (<code>{c.from_user_id}</code>)\n"
            f"Kimga: {against_name} (<code>{c.against_user_id}</code>)\n"
            f"Matn: {c.text[:300]}\n"
            f"Sana: {c.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=complaint_review_kb(c.id))


@router.callback_query(F.data.startswith("complaint_close_"))
async def close_complaint(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    complaint_id = int(callback.data.split("_")[2])
    await queries.close_complaint(session, complaint_id, callback.from_user.id)
    await queries.add_log(session, callback.from_user.id, "complaint_closed", f"id: {complaint_id}")
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Ko'rib chiqildi.</b>",
        parse_mode="HTML",
    )
    await callback.answer("Shikoyat yopildi.")


@router.callback_query(F.data.startswith("complaint_ban_"))
async def complaint_ban(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    complaint_id = int(callback.data.split("_")[2])
    result = await session.execute(select(Complaint).where(Complaint.id == complaint_id))
    c = result.scalar_one_or_none()
    if not c:
        await callback.answer("Shikoyat topilmadi.")
        return

    await queries.ban_user(session, c.against_user_id, True)
    await queries.close_complaint(session, complaint_id, callback.from_user.id)
    await queries.add_log(session, callback.from_user.id, "complaint_ban", f"banned: {c.against_user_id}")
    await callback.message.edit_text(
        callback.message.text + f"\n\n🚫 <b>Foydalanuvchi {c.against_user_id} bloklandi.</b>",
        parse_mode="HTML",
    )
    try:
        await bot.send_message(c.against_user_id, "🚫 Siz shikoyat asosida bloklandingiz.")
    except Exception:
        pass
    await callback.answer("Bloklandi.")


# ============ BOSH SAHIFA ============

@router.message(F.text == "🏠 Bosh sahifa")
async def back_home(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return
    await message.answer("Bosh sahifaga qaytdingiz.", reply_markup=main_menu_kb())
