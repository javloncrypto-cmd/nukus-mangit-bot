from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import Optional


# ============ UMUMIY ============

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
        keyboard=[
            [KeyboardButton(text="🙋 Yo'lovchi"), KeyboardButton(text="🚗 Haydovchi")],
        ],
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


def skip_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭️ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
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
    builder.button(text="✏️ Odam soni o'zgartirish", callback_data=f"d_change_{ann_id}")
    builder.button(text="✍️ Tahrirlash", callback_data=f"d_edit_{ann_id}")
    builder.button(text="✅ Hamma joy to'ldi", callback_data=f"d_full_{ann_id}")
    builder.adjust(2, 1, 1)
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


# ============ ADMIN ============

def admin_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📊 Statistika")
    builder.button(text="🚫 Qora ro'yxat")
    builder.button(text="📋 Shikoyatlar")
    builder.button(text="🔓 Blok ochish")
    builder.button(text="🏠 Bosh sahifa")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


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
