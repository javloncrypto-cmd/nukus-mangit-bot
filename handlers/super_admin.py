from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from db import queries
from keyboards.keyboards import (
    super_admin_kb, main_menu_kb, admin_role_select_kb, settings_kb,
)

router = Router()


class SuperAdminForm(StatesGroup):
    waiting_add_admin_id = State()
    waiting_setting_value = State()


async def check_super(session: AsyncSession, user_id: int) -> bool:
    return await queries.is_super_admin(session, user_id)


# ============ PANEL ============

@router.message(Command("superadmin"))
async def super_panel(message: Message, session: AsyncSession):
    if not await check_super(session, message.from_user.id):
        await message.answer("⛔ Ruxsat yo'q.")
        return
    await message.answer("👑 Super Admin panel:", reply_markup=super_admin_kb())


# ============ FOYDALANUVCHILAR RO'YXATI ============

PER_PAGE = 20

ROLE_LABELS = {
    "driver": "Haydovchi",
    "passenger": "Yolovchi",
    None: "Belgilanmagan",
}


async def _users_page_text(session, page: int) -> tuple[str, int]:
    total = await queries.get_all_users_count(session)
    users = await queries.get_all_users(session, offset=page * PER_PAGE, limit=PER_PAGE)

    if not users:
        return "👤 Foydalanuvchilar topilmadi.", 0

    start = page * PER_PAGE + 1
    end = min(start + PER_PAGE - 1, total)
    text = f"👤 <b>Foydalanuvchilar ({start}–{end} / {total}):</b>\n\n"

    for u in users:
        ban_mark = " 🚫" if u.is_banned else ""
        role = ROLE_LABELS.get(u.role, u.role or "—")
        phone = u.phone or "—"
        block = (
            f"<b>{u.full_name}</b>{ban_mark}\n"
            f"  📞 {phone}\n"
            f"  🆔 <code>{u.user_id}</code> | {role}\n\n"
        )
        if len(text) + len(block) > 3800:
            text += "..."
            break
        text += block

    return text, total


@router.message(F.text == "👤 Foydalanuvchilar")
async def users_list(message: Message, session: AsyncSession):
    if not await check_super(session, message.from_user.id):
        return

    try:
        from keyboards.keyboards import users_list_nav_kb
        text, total = await _users_page_text(session, 0)
        await message.answer(text, parse_mode="HTML", reply_markup=users_list_nav_kb(0, total, PER_PAGE))
    except Exception as e:
        await message.answer(f"❌ Xato yuz berdi: {e}")


@router.callback_query(F.data.startswith("users_page_"))
async def users_page(callback: CallbackQuery, session: AsyncSession):
    if not await check_super(session, callback.from_user.id):
        await callback.answer("Ruxsat yoq.", show_alert=True)
        return

    try:
        page = int(callback.data.split("_")[2])
        from keyboards.keyboards import users_list_nav_kb
        text, total = await _users_page_text(session, page)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=users_list_nav_kb(page, total, PER_PAGE))
    except Exception as e:
        await callback.message.answer(f"❌ Xato: {e}")
    await callback.answer()


@router.callback_query(F.data.startswith("sa_ban_"))
async def sa_ban_user(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await check_super(session, callback.from_user.id):
        await callback.answer("Ruxsat yoq.", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    user = await queries.get_user(session, user_id)
    await queries.ban_user(session, user_id, True)
    await queries.add_log(session, callback.from_user.id, "sa_ban", f"target: {user_id}")
    name = user.full_name if user else user_id
    await callback.message.edit_text(f"🚫 <b>{name}</b> (<code>{user_id}</code>) bloklandi.", parse_mode="HTML")
    try:
        await bot.send_message(user_id, "🚫 Siz admin tomonidan bloklandingiz.")
    except Exception:
        pass
    await callback.answer("Bloklandi.")


@router.callback_query(F.data.startswith("sa_unban_"))
async def sa_unban_user(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await check_super(session, callback.from_user.id):
        await callback.answer("Ruxsat yoq.", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    user = await queries.get_user(session, user_id)
    await queries.ban_user(session, user_id, False)
    await queries.add_log(session, callback.from_user.id, "sa_unban", f"target: {user_id}")
    name = user.full_name if user else user_id
    await callback.message.edit_text(f"✅ <b>{name}</b> (<code>{user_id}</code>) blokdan chiqarildi.", parse_mode="HTML")
    try:
        await bot.send_message(user_id, "✅ Sizning blokingiz olib tashlandi.")
    except Exception:
        pass
    await callback.answer("Blok ochildi.")


# ============ ADMINLAR ============

@router.message(F.text == "👥 Adminlar")
async def list_admins(message: Message, session: AsyncSession, state: FSMContext):
    if not await check_super(session, message.from_user.id):
        return

    admins = await queries.get_all_admins(session)
    if not admins:
        text = "Hozircha adminlar yo'q.\n\n"
    else:
        text = "👥 <b>Adminlar ro'yxati:</b>\n\n"
        for a in admins:
            role_icon = "👑" if a.role == "super_admin" else "👮"
            name = a.user.full_name if a.user else "Noma'lum"
            text += f"{role_icon} {name} — <code>{a.user_id}</code> [{a.role}]\n"
        text += "\n"

    text += "Admin qo'shish yoki o'chirish uchun foydalanuvchi ID sini yuboring:"
    await state.set_state(SuperAdminForm.waiting_add_admin_id)
    await message.answer(text, parse_mode="HTML")


@router.message(SuperAdminForm.waiting_add_admin_id)
async def process_admin_id(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=super_admin_kb())
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("Noto'g'ri ID. Raqam kiriting yoki /cancel:")
        return

    user = await queries.get_user(session, target_id)
    if not user:
        await message.answer(f"❌ ID {target_id} topilmadi. Foydalanuvchi ro'yxatdan o'tganmi?")
        return

    await state.clear()
    await message.answer(
        f"👤 {user.full_name} (<code>{target_id}</code>) uchun rol tanlang:",
        parse_mode="HTML",
        reply_markup=admin_role_select_kb(target_id),
    )


@router.callback_query(F.data.startswith("set_role_admin_"))
async def set_role_admin(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await check_super(session, callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    target_id = int(callback.data.split("_")[3])
    await queries.add_admin(session, target_id, "admin", callback.from_user.id)
    await queries.add_log(session, callback.from_user.id, "admin_added", f"user_id: {target_id}, role: admin")
    user = await queries.get_user(session, target_id)
    await callback.message.edit_text(f"✅ {user.full_name if user else target_id} — Admin qilindi.")
    try:
        await bot.send_message(target_id, "👮 Siz Admin etib tayinlandingiz! /admin buyrug'ini ishlatishingiz mumkin.")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("set_role_super_"))
async def set_role_super(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await check_super(session, callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    target_id = int(callback.data.split("_")[3])
    await queries.add_admin(session, target_id, "super_admin", callback.from_user.id)
    await queries.add_log(session, callback.from_user.id, "super_admin_added", f"user_id: {target_id}")
    user = await queries.get_user(session, target_id)
    await callback.message.edit_text(f"✅ {user.full_name if user else target_id} — Super Admin qilindi.")
    try:
        await bot.send_message(target_id, "👑 Siz Super Admin etib tayinlandingiz! /superadmin buyrug'ini ishlatishingiz mumkin.")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("remove_admin_"))
async def remove_admin(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not await check_super(session, callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    target_id = int(callback.data.split("_")[2])
    await queries.remove_admin(session, target_id)
    await queries.add_log(session, callback.from_user.id, "admin_removed", f"user_id: {target_id}")
    user = await queries.get_user(session, target_id)
    await callback.message.edit_text(f"✅ {user.full_name if user else target_id} — Adminlikdan olindi.")
    try:
        await bot.send_message(target_id, "ℹ️ Sizning admin huquqingiz bekor qilindi.")
    except Exception:
        pass
    await callback.answer()


# ============ SOZLAMALAR ============

@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: Message, session: AsyncSession):
    if not await check_super(session, message.from_user.id):
        return

    settings = await queries.get_all_settings(session)
    text = "⚙️ <b>Bot sozlamalari:</b>\n\n"
    for s in settings:
        desc = f" — {s.description}" if s.description else ""
        text += f"<code>{s.key}</code>: <b>{s.value}</b>{desc}\n"

    await message.answer(text, parse_mode="HTML", reply_markup=settings_kb(settings))


@router.callback_query(F.data.startswith("edit_setting_"))
async def edit_setting_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await check_super(session, callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    key = callback.data[len("edit_setting_"):]
    current = await queries.get_setting(session, key)
    await state.update_data(setting_key=key)
    await state.set_state(SuperAdminForm.waiting_setting_value)
    await callback.message.answer(
        f"⚙️ <b>{key}</b>\nHozirgi qiymat: <code>{current}</code>\n\nYangi qiymatni yuboring (/cancel bekor qilish):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SuperAdminForm.waiting_setting_value)
async def edit_setting_done(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=super_admin_kb())
        return
    data = await state.get_data()
    key = data["setting_key"]
    await queries.set_setting(session, key, message.text.strip(), message.from_user.id)
    await queries.add_log(session, message.from_user.id, "setting_changed", f"{key}={message.text.strip()}")
    await state.clear()
    await message.answer(f"✅ <b>{key}</b> = <code>{message.text.strip()}</code> saqlandi.", parse_mode="HTML", reply_markup=super_admin_kb())


# ============ TIZIM LOGLARI ============

@router.message(F.text == "📜 Tizim loglari")
async def system_logs(message: Message, session: AsyncSession):
    if not await check_super(session, message.from_user.id):
        return

    logs = await queries.get_recent_logs(session, limit=30)
    if not logs:
        await message.answer("Loglar yo'q.")
        return

    text = "📜 <b>Oxirgi 30 ta log:</b>\n\n"
    for log in logs:
        time_str = log.created_at.strftime("%d.%m %H:%M")
        uid = f"<code>{log.user_id}</code>" if log.user_id else "tizim"
        details = f" — {log.details[:60]}" if log.details else ""
        text += f"[{time_str}] {uid} → <b>{log.action}</b>{details}\n"

    await message.answer(text[:4000], parse_mode="HTML")


# ============ FAOL E'LONLAR (Super Admin) ============

@router.message(F.text == "📢 Faol e'lonlar")
async def all_active_announcements(message: Message, session: AsyncSession):
    if not await queries.is_admin_or_super(session, message.from_user.id):
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
            f"   {ann.passengers_count} joy | {ann.created_at.strftime('%d.%m %H:%M')}\n\n"
        )

    await message.answer(text[:4000], parse_mode="HTML")


# ============ STATISTIKA (Super Admin) ============

@router.message(F.text == "📊 Statistika")
async def stats(message: Message, session: AsyncSession):
    if not await queries.is_admin_or_super(session, message.from_user.id):
        return

    total_users = await queries.get_all_users_count(session)
    today_anns = await queries.get_today_announcements_count(session)
    direction_stats = await queries.get_avg_price_stats(session)
    top_drivers = await queries.get_top_drivers(session)
    admins = await queries.get_all_admins(session)

    top_text = ""
    for i, (driver_id, avg, cnt) in enumerate(top_drivers, 1):
        top_text += f"  {i}. ID: {driver_id} — ⭐ {avg:.1f} ({cnt} baholash)\n"

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
        f"👥 Adminlar:\n{admin_text or '  —'}\n"
        f"🏆 Top haydovchilar:\n{top_text or '  Hali malumot yoq'}"
    )
    await message.answer(text, parse_mode="HTML")
