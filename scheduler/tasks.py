from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import async_session_maker
from db import queries
from keyboards.keyboards import (
    passenger_confirm_kb, driver_interval_kb,
    driver_feedback_kb, rating_kb,
)


async def check_passenger_announcements(bot: Bot):
    """30 daqiqa o'tgan yo'lovchi e'lonlarini tekshiradi"""
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from db.database import Announcement

    cutoff = datetime.utcnow() - timedelta(minutes=10)

    async with async_session_maker() as session:
        result = await session.execute(
            select(Announcement).where(
                and_(
                    Announcement.status == "active",
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
                    "⏱ 30 daqiqa o'tdi. E'lonni yakunlaymizmi?",
                    reply_markup=passenger_confirm_kb(ann.id),
                )
            except Exception:
                pass


async def check_driver_interval(bot: Bot):
    """1 daqiqa o'tgan haydovchi e'lonlarini tekshiradi"""
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from db.database import Announcement

    # Check announcements created 1 minute ago that haven't been checked
    cutoff_min = datetime.utcnow() - timedelta(minutes=1)
    cutoff_max = datetime.utcnow() - timedelta(seconds=30)

    async with async_session_maker() as session:
        result = await session.execute(
            select(Announcement).where(
                and_(
                    Announcement.status == "active",
                    Announcement.created_at <= cutoff_min,
                    Announcement.created_at >= cutoff_max,
                )
            )
        )
        anns = result.scalars().all()

        for ann in anns:
            user = await queries.get_user(session, ann.user_id)
            if not user or user.role != "driver":
                continue
            try:
                await bot.send_message(
                    ann.user_id,
                    "🚗 Yo'lovchi topildimi?",
                    reply_markup=driver_interval_kb(ann.id),
                )
            except Exception:
                pass


async def check_driver_feedback(bot: Bot):
    """1 soat avval yakunlangan haydovchi e'lonlari uchun feedback"""
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from db.database import Announcement

    cutoff_min = datetime.utcnow() - timedelta(hours=1)
    cutoff_max = datetime.utcnow() - timedelta(minutes=50)

    async with async_session_maker() as session:
        result = await session.execute(
            select(Announcement).where(
                and_(
                    Announcement.status == "completed",
                    Announcement.created_at <= cutoff_min,
                    Announcement.created_at >= cutoff_max,
                )
            )
        )
        anns = result.scalars().all()

        for ann in anns:
            user = await queries.get_user(session, ann.user_id)
            if not user or user.role != "driver":
                continue
            try:
                await bot.send_message(
                    ann.user_id,
                    "🚗 Safar yakunlandimi?",
                    reply_markup=driver_feedback_kb(ann.id),
                )
            except Exception:
                pass


async def cleanup_expired_announcements(bot: Bot):
    """24 soatdan o'tgan e'lonlarni tozalaydi"""
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


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    scheduler.add_job(
        check_passenger_announcements,
        trigger="interval",
        minutes=5,
        args=[bot],
        id="passenger_check",
    )

    scheduler.add_job(
        check_driver_interval,
        trigger="interval",
        minutes=1,
        args=[bot],
        id="driver_interval",
    )

    scheduler.add_job(
        check_driver_feedback,
        trigger="interval",
        minutes=10,
        args=[bot],
        id="driver_feedback",
    )

    scheduler.add_job(
        cleanup_expired_announcements,
        trigger="interval",
        hours=1,
        args=[bot],
        id="cleanup",
    )

    return scheduler
