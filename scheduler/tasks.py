from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from db.database import async_session_maker
from db import queries
from keyboards.keyboards import (
    passenger_confirm_kb, driver_interval_kb,
    driver_feedback_kb, rating_kb,
)


async def check_passenger_announcements(bot: Bot):
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from db.database import Announcement

    async with async_session_maker() as session:
        minutes = int(await queries.get_setting(session, "passenger_check_min", "30"))
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        result = await session.execute(
            select(Announcement).where(
                and_(Announcement.status == "active", Announcement.created_at <= cutoff)
            )
        )
        anns = result.scalars().all()

        for ann in anns:
            user = await queries.get_user(session, ann.user_id)
            if not user or user.role != "passenger":
                continue
            try:
                await bot.send_message(
                    ann.user_id,
                    f"⏱ {minutes} daqiqa o'tdi. E'lonni yakunlaymizmi?",
                    reply_markup=passenger_confirm_kb(ann.id),
                )
            except Exception:
                pass


async def check_driver_interval(bot: Bot):
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from db.database import Announcement

    async with async_session_maker() as session:
        minutes = int(await queries.get_setting(session, "driver_check_min", "1"))
        cutoff_min = datetime.utcnow() - timedelta(minutes=minutes)
        cutoff_max = datetime.utcnow() - timedelta(seconds=max(30, minutes * 60 - 30))

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
    from datetime import datetime, timedelta
    from sqlalchemy import select, and_
    from db.database import Announcement

    async with async_session_maker() as session:
        cutoff_min = datetime.utcnow() - timedelta(hours=1)
        cutoff_max = datetime.utcnow() - timedelta(minutes=50)

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
    from config import CHANNEL_ID

    async with async_session_maker() as session:
        hours = int(await queries.get_setting(session, "ann_expire_hours", "24"))
        from datetime import datetime, timedelta
        from sqlalchemy import select, and_
        from db.database import Announcement

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await session.execute(
            select(Announcement).where(
                and_(Announcement.status == "active", Announcement.created_at < cutoff)
            )
        )
        anns = result.scalars().all()

        for ann in anns:
            if ann.channel_msg_id:
                try:
                    await bot.delete_message(CHANNEL_ID, ann.channel_msg_id)
                except Exception:
                    pass
            await queries.update_announcement_status(session, ann.id, "expired")
            await queries.add_log(session, None, "ann_expired", f"ann_id: {ann.id}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    scheduler.add_job(check_passenger_announcements, trigger="interval", minutes=5, args=[bot], id="passenger_check")
    scheduler.add_job(check_driver_interval,          trigger="interval", minutes=1, args=[bot], id="driver_interval")
    scheduler.add_job(check_driver_feedback,          trigger="interval", minutes=10, args=[bot], id="driver_feedback")
    scheduler.add_job(cleanup_expired_announcements,  trigger="interval", hours=1,   args=[bot], id="cleanup")

    return scheduler
