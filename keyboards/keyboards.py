from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import Optional, List


# ============ ASOSIY MENYU ============

def main_menu_kb() -> ReplyKeyboardMarkup:
    """
    V1: Yo'lovchi yo'nalish tugmalari va profil.
    V2 (kelajak): Haydovchi tugmasi va rol o'zgartirish qo'shiladi.
    """
    builder = ReplyKeyboardBuilder()
    builder.button(text="🚌 Nukus ➡️ Mangit")
    builder.button(text="🚌 Mangit ➡️ Nukus")
    builder.button(text="ℹ️ Ma'lumotim")
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)


def share_contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def share_location_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Joylashuvimni yuborish", request_location=True)],
            [KeyboardButton(text="⏭️ O'tkazib yuborish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )


# ============ YO'LOVCHI ============

def passengers_count_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 5):
        builder.button(text=str(i), callback_data=f"pcount_{i}")
    builder.adjust(4)
    return builder.as_markup()


def passenger_confirm_kb(ann_id: int) -> InlineKeyboardMarkup:
    """30 daqiqa o'tganda yo'lovchiga yuboriladigan tugmalar."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, yakunlaymiz", callback_data=f"p_done_{ann_id}")
    builder.button(text="🔄 Yo'q, qayta yuklash", callback_data=f"p_reload_{ann_id}")
    builder.adjust(2)
    return builder.as_markup()


def active_ann_kb(ann_id: int) -> InlineKeyboardMarkup:
    """Faol e'lon mavjud bo'lganda ko'rsatiladigan tugmalar."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yakunlash", callback_data=f"p_done_{ann_id}")
    builder.button(text="❌ Bekor qilish", callback_data=f"cancel_ann_{ann_id}")
    builder.adjust(2)
    return builder.as_markup()


# ============ PROFIL ============

def profile_edit_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Ismni o'zgartirish", callback_data="profile_edit_name")
    builder.button(text="📱 Telefon o'zgartirish", callback_data="profile_edit_phone")
    builder.adjust(1)
    return builder.as_markup()


# ============ ADMIN ============

def admin_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Statistika")
    builder.button(text="🚫 Qora ro'yxat")
    builder.button(text="📋 Shikoyatlar")
    builder.button(text="🔓 Blok ochish")
    builder.button(text="📢 Faol e'lonlar")
    builder.button(text="🏠 Bosh sahifa")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def super_admin_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Statistika")
    builder.button(text="👤 Foydalanuvchilar")
    builder.button(text="👥 Adminlar")
    builder.button(text="⚙️ Sozlamalar")
    builder.button(text="📢 Faol e'lonlar")
    builder.button(text="📜 Tizim loglari")
    builder.button(text="🏠 Bosh sahifa")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def complaint_review_kb(complaint_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ko'rib chiqildi", callback_data=f"complaint_close_{complaint_id}")
    builder.button(text="🚫 Bloklash", callback_data=f"complaint_ban_{complaint_id}")
    builder.adjust(2)
    return builder.as_markup()


def admin_role_select_kb(target_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👮 Admin", callback_data=f"set_role_admin_{target_id}")
    builder.button(text="👑 Super Admin", callback_data=f"set_role_super_{target_id}")
    builder.button(text="❌ Adminlikdan olish", callback_data=f"remove_admin_{target_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def settings_kb(settings: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in settings:
        builder.button(text=f"✏️ {s.key}", callback_data=f"edit_setting_{s.key}")
    builder.adjust(1)
    return builder.as_markup()


def users_list_nav_kb(page: int, total: int, per_page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="⬅️ Oldingi", callback_data=f"users_page_{page - 1}")
    if (page + 1) * per_page < total:
        builder.button(text="Keyingi ➡️", callback_data=f"users_page_{page + 1}")
    builder.adjust(2)
    return builder.as_markup()


# ============ V2 UCHUN SAQLANGAN (hozir ishlatilmaydi) ============
# Quyidagi funksiyalar V2 da haydovchi qo'shilganda yoqiladi:

# def role_select_kb() -> ReplyKeyboardMarkup: ...
# def driver_control_kb(ann_id: int) -> InlineKeyboardMarkup: ...
# def driver_interval_kb(ann_id: int) -> InlineKeyboardMarkup: ...
# def driver_seats_kb(ann_id: int) -> InlineKeyboardMarkup: ...
# def driver_feedback_kb(ann_id: int) -> InlineKeyboardMarkup: ...
# def rating_kb(driver_id: int) -> InlineKeyboardMarkup: ...
