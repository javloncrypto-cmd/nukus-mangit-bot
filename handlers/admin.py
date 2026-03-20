from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from db import queries
from keyboards.keyboards import admin_kb, main_menu_kb
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminForm(StatesGroup):
    waiting_ban_id = State()
    waiting_unban_id = State()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    await message.answer("🔐 Admin panel:", reply_markup=admin_kb())


@router.message(F.text == "📊 Statistika")
async def stats(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    total_users = await queries.get_all_users_count(session)
    today_anns = await queries.get_today_announcements_count(session)
    direction_stats = await queries.get_avg_price_stats(session)
    top_drivers = await queries.get_top_drivers(session)

    top_text = ""
    for i, (driver_id, avg, cnt) in enumerate(top_drivers, 1):
        top_text += f"  {i}. ID: {driver_id} — ⭐ {avg:.1f} ({cnt} baholash)\n"

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👤 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"📢 Bugungi e'lonlar: <b>{today_anns}</b>\n\n"
        f"📍 Faol e'lonlar:\n"
        f"  • Nukus→Mangit: <b>{direction_stats['nukus_mangit']}</b>\n"
        f"  • Mangit→Nukus: <b>{direction_stats['mangit_nukus']}</b>\n\n"
        f"🏆 Top haydovchilar:\n{top_text if top_text else '  Hali malumot yoq'}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🚫 Qora ro'yxat")
async def blacklist(message: Message, session: AsyncSession, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    low_rating = await queries.get_low_rating_drivers(session)
    if not low_rating:
        await message.answer("Hozircha reytingi past haydovchi yo'q.")
        return

    text = "🚫 <b>Past reytingli haydovchilar:</b>\n\n"
    for driver_id, avg_score in low_rating:
        text += f"• ID: <code>{driver_id}</code> — ⭐ {avg_score:.1f}\n"

    await message.answer(text, parse_mode="HTML")
    await state.set_state(AdminForm.waiting_ban_id)
    await message.answer("Blok qilish uchun foydalanuvchi ID sini yuboring (yoki /cancel):")


@router.message(AdminForm.waiting_ban_id)
async def ban_user_action(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    try:
        user_id = int(message.text)
        await queries.ban_user(session, user_id, True)
        await state.clear()
        await message.answer(f"✅ {user_id} bloklandi.")
    except ValueError:
        await message.answer("Noto'g'ri ID. Raqam kiriting.")


@router.message(F.text == "🔓 Blok ochish")
async def unban_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminForm.waiting_unban_id)
    await message.answer("Blokni ochish uchun foydalanuvchi ID sini yuboring:")


@router.message(AdminForm.waiting_unban_id)
async def unban_user_action(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        return
    try:
        user_id = int(message.text)
        await queries.ban_user(session, user_id, False)
        await state.clear()
        await message.answer(f"✅ {user_id} blokdan chiqarildi.")
    except ValueError:
        await message.answer("Noto'g'ri ID.")


@router.message(F.text == "📋 Shikoyatlar")
async def complaints(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    ratings = await queries.get_complaints(session)
    if not ratings:
        await message.answer("Hozircha shikoyat yo'q.")
        return

    text = "📋 <b>Salbiy izohlar:</b>\n\n"
    for r in ratings:
        text += f"• Haydovchi: <code>{r.driver_id}</code>\n  ⭐{r.score} — {r.comment}\n\n"
    await message.answer(text[:4000], parse_mode="HTML")


@router.message(F.text == "🏠 Bosh sahifa")
async def back_home(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    user = await queries.get_user(session, message.from_user.id)
    role = user.role if user else None
    await message.answer("Bosh sahifaga qaytdingiz.", reply_markup=main_menu_kb(role))
