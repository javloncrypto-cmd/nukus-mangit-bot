from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import Optional


# ============ ASOSIY MENYU ============

def main_menu_kb(role: Optional[str] = None) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🚌 Nukus ➡️ Mangit")
    builder.button(text="🚌 Mangit ➡️ Nukus")
    builder.button(text="🚗 Haydovchi e'loni")
    builder.button(text="ℹ️ Ma'lumotim")
    builder.button(text="🔄 Rolni o'zgartirish")
    builder.adjust(2, 1, 2)
    return builder.as_markup(resize_keyboard=True)


def role_select_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🙋 Yo'lovchi"), KeyboardButton(text="🚗 Haydovchi")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


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
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, yakunlaymiz", callback_data=f"p_done_{ann_id}")
    builder.button(text="🔄 Yo'q, qayta yuklash", callback_data=f"p_reload_{ann_id}")
    builder.adjust(2)
    return builder.as_markup()


# ============ HAYDOVCHI ============

def driver_control_kb(ann_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Qayta yuklash", callback_data=f"d_reload_{ann_id}")
    builder.button(text="✏️ Joy soni", callback_data=f"d_change_{ann_id}")
    builder.button(text="✍️ Tahrirlash", callback_data=f"d_edit_{ann_id}")
    builder.button(text="✅ To'ldi", callback_data=f"d_full_{ann_id}")
    builder.adjust(2, 2)
    return builder.as_markup()


def driver_interval_kb(ann_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, topildi", callback_data=f"d_found_{ann_id}")
    builder.button(text="❌ Yo'q", callback_data=f"d_notfound_{ann_id}")
    builder.button(text="🔄 Qayta yuklash", callback_data=f"d_reload_{ann_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def driver_seats_kb(ann_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(1, 5):
        builder.button(text=str(i), callback_data=f"d_seats_{ann_id}_{i}")
    builder.adjust(4)
    return builder.as_markup()


def driver_feedback_kb(ann_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, yakunlandi", callback_data=f"d_trip_done_{ann_id}")
    builder.button(text="❌ Yo'q", callback_data=f"d_trip_cancel_{ann_id}")
    builder.adjust(2)
    return builder.as_markup()


# ============ REYTING ============

def rating_kb(driver_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for score in range(1, 6):
        stars = "⭐" * score
        builder.button(text=stars, callback_data=f"rate_{driver_id}_{score}")
    builder.adjust(5)
    return builder.as_markup()


# ============ SHIKOYAT ============

def complaint_kb(against_user_id: int, ann_id: Optional[int] = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    ann_part = ann_id if ann_id else 0
    builder.button(text="📝 Shikoyat yuborish", callback_data=f"complaint_{against_user_id}_{ann_part}")
    return builder.as_markup()


def complaint_review_kb(complaint_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ko'rib chiqildi", callback_data=f"complaint_close_{complaint_id}")
    builder.button(text="🚫 Foydalanuvchini bloklash", callback_data=f"complaint_ban_{complaint_id}")
    builder.adjust(1)
    return builder.as_markup()


# ============ PROFIL ============

def profile_edit_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Ismni o'zgartirish", callback_data="profile_edit_name")
    builder.button(text="📱 Telefon yangilash", callback_data="profile_edit_phone")
    builder.adjust(1)
    return builder.as_markup()


# ============ E'LON TARIXI ============

def ann_history_kb(ann_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Batafsil", callback_data=f"ann_detail_{ann_id}")
    return builder.as_markup()


# ============ FAOL E'LON ============

def active_ann_kb(ann_id: int, role: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if role == "passenger":
        builder.button(text="✅ Yakunlash", callback_data=f"p_done_{ann_id}")
        builder.button(text="❌ Bekor qilish", callback_data=f"cancel_ann_{ann_id}")
    else:
        builder.button(text="✅ Yakunlash", callback_data=f"d_full_{ann_id}")
        builder.button(text="❌ Bekor qilish", callback_data=f"cancel_ann_{ann_id}")
    builder.adjust(2)
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


# ============ SUPER ADMIN ============

def super_admin_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Statistika")
    builder.button(text="👥 Adminlar")
    builder.button(text="👤 Foydalanuvchilar")
    builder.button(text="⚙️ Sozlamalar")
    builder.button(text="📜 Tizim loglari")
    builder.button(text="📢 Faol e'lonlar")
    builder.button(text="🚫 Qora ro'yxat")
    builder.button(text="📋 Shikoyatlar")
    builder.button(text="🏠 Bosh sahifa")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def admin_role_select_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👮 Admin qilish", callback_data=f"set_role_admin_{user_id}")
    builder.button(text="🔑 Super Admin qilish", callback_data=f"set_role_super_{user_id}")
    builder.button(text="❌ Adminlikdan olish", callback_data=f"remove_admin_{user_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def users_list_nav_kb(page: int, total: int, per_page: int = 20) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="⬅️ Oldingi", callback_data=f"users_page_{page - 1}")
    if (page + 1) * per_page < total:
        builder.button(text="Keyingi ➡️", callback_data=f"users_page_{page + 1}")
    builder.adjust(2)
    return builder.as_markup()


def user_detail_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚫 Bloklash", callback_data=f"sa_ban_{user_id}")
    builder.button(text="✅ Blokdan chiqarish", callback_data=f"sa_unban_{user_id}")
    builder.button(text="👮 Admin qilish", callback_data=f"set_role_admin_{user_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def settings_kb(settings: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in settings:
        builder.button(text=f"✏️ {s.key}", callback_data=f"edit_setting_{s.key}")
    builder.adjust(1)
    return builder.as_markup()
