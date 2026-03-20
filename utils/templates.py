from db.database import Announcement, User


DIRECTION_LABELS = {
    "nukus_mangit": "Nukus ➡️ Mangit",
    "mangit_nukus": "Mangit ➡️ Nukus",
}


def passenger_announcement_text(ann: Announcement, user: User) -> str:
    direction = DIRECTION_LABELS.get(ann.direction, ann.direction)
    note_line = f"\n📝 Izoh: {ann.note}" if ann.note else ""
    time_str = ann.created_at.strftime("%H:%M")
    return (
        f"🙋 <b>YO'LOVCHI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Yo'nalish: {direction}\n"
        f"👤 Ismi: {user.full_name}\n"
        f"📞 Tel: {user.phone}\n"
        f"👥 Odamlar: {ann.passengers_count} kishi\n"
        f"💰 Narx: {ann.price}{note_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ Joylashtirildi: {time_str}"
    )


def driver_announcement_text(ann: Announcement, user: User) -> str:
    direction = DIRECTION_LABELS.get(ann.direction, ann.direction)
    note_line = f"\n📝 Izoh: {ann.note}" if ann.note else ""
    time_str = ann.created_at.strftime("%H:%M")
    return (
        f"🚗 <b>HAYDOVCHI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Yo'nalish: {direction}\n"
        f"👤 Ismi: {user.full_name}\n"
        f"📞 Tel: {user.phone}\n"
        f"👥 Bo'sh joy: {ann.passengers_count} ta\n"
        f"💰 Narx: {ann.price}{note_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ Joylashtirildi: {time_str}"
    )
