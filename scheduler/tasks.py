from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from db.database import async_session_maker
from db import queries
from keyboards.keyboards import passenger_confirm_kb


# ============ YO'LOVCHI TEKSHIRUVI ============

async def check_passenger_announcements(bot: Bot):
    """
    30 daqiqa o'tgan faol yo'lovchi e'lonlarini tekshiradi.
    Egasiga yakunlash/qayta yuklash tugmalari yuboriladi.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from db.database import Announcement

    cutoff = datetime.utcnow() - timedelta(minutes=30)

    async with async_session_maker() as session:
        result = await session.execute(
            select(Announcement).where(
                and_(
                    Announcement.status == "active",
                    Announcement.ann_type == "passenger",
                    Announcement.created_at <= cutoff,
                )
            )
        )
        anns = result.scalars().all()

        for ann in anns:
            user = await queries.get_user(session, ann.user_id)
            if not user:
                continue
            try:
                await bot.send_message(
                    ann.user_id,
                    "⏱ 30 daqiqa o'tdi. Haydovchi topildimi?\n"
                    "E'lonni yakunlaymizmi yoki qayta yuklaymizmi?",
                    reply_markup=passenger_confirm_kb(ann.id),
                )
            except Exception:
                pass


# ============ ESKIRGAN E'LONLARNI TOZALASH ============

async def cleanup_expired_announcements(bot: Bot):
    """24 soatdan o'tgan faol e'lonlarni avtomatik yopadi."""
    from config import CHANNEL_ID

    async with async_session_maker() as session:
        anns = await queries.get_expired_announcements(session)
        for ann in anns:
            if ann.channel_msg_id:
                try:
                    await bot.delete_message(CHANNEL_ID, ann.channel_msg_id)
                except Exception:
                    pass
            await queries.update_announcement_status(session, ann.id, "expired")
            # Foydalanuvchiga xabar berish
            try:
                await bot.send_message(
                    ann.user_id,
                    "⏰ E'loningiz 24 soat muddati o'tgani sababli avtomatik yopildi.\n"
                    "Kerak bo'lsa yangi e'lon bering.",
                )
            except Exception:
                pass


# ============ SCHEDULER SOZLASH ============

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # Yo'lovchi e'lonlarini 5 daqiqada bir tekshirish
    scheduler.add_job(
        check_passenger_announcements,
        trigger="interval",
        minutes=5,
        args=[bot],
        id="passenger_check",
    )

    # Eskirgan e'lonlarni soatda bir tozalash
    scheduler.add_job(
        cleanup_expired_announcements,
        trigger="interval",
        hours=1,
        args=[bot],
        id="cleanup",
    )

    # ================================================================
    # V2 UCHUN SAQLANGAN VAZIFALAR (hozir o'chirilgan):
    #
    # scheduler.add_job(
    #     check_driver_interval,       # 1 daqiqada haydovchiga so'rov
    #     trigger="interval", minutes=1, args=[bot], id="driver_interval",
    # )
    # scheduler.add_job(
    #     check_driver_feedback,       # 1 soat keyin safar tugadimi?
    #     trigger="interval", minutes=10, args=[bot], id="driver_feedback",
    # )
    # ================================================================

    return scheduler
