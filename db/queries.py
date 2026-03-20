from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from db.database import User, Announcement, Rating
from datetime import datetime, timedelta


# ==================== USER QUERIES ====================

async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, user_id: int, full_name: str) -> User:
    user = User(user_id=user_id, full_name=full_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_phone(session: AsyncSession, user_id: int, phone: str):
    await session.execute(
        update(User).where(User.user_id == user_id).values(phone=phone)
    )
    await session.commit()


async def update_user_role(session: AsyncSession, user_id: int, role: str):
    await session.execute(
        update(User).where(User.user_id == user_id).values(role=role)
    )
    await session.commit()


async def ban_user(session: AsyncSession, user_id: int, is_banned: bool = True):
    await session.execute(
        update(User).where(User.user_id == user_id).values(is_banned=is_banned)
    )
    await session.commit()


async def get_all_users_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()


# ==================== ANNOUNCEMENT QUERIES ====================

async def create_announcement(
    session: AsyncSession,
    user_id: int,
    direction: str,
    passengers_count: int,
    price: str,
    note: Optional[str] = None,
    location_lat: Optional[float] = None,
    location_lon: Optional[float] = None,
) -> Announcement:
    ann = Announcement(
        user_id=user_id,
        direction=direction,
        passengers_count=passengers_count,
        price=price,
        note=note,
        location_lat=location_lat,
        location_lon=location_lon,
    )
    session.add(ann)
    await session.commit()
    await session.refresh(ann)
    return ann


async def get_announcement(session: AsyncSession, ann_id: int) -> Optional[Announcement]:
    result = await session.execute(
        select(Announcement)
        .options(selectinload(Announcement.user))
        .where(Announcement.id == ann_id)
    )
    return result.scalar_one_or_none()


async def get_active_announcement_by_user(
    session: AsyncSession, user_id: int
) -> Optional[Announcement]:
    result = await session.execute(
        select(Announcement).where(
            and_(Announcement.user_id == user_id, Announcement.status == "active")
        )
    )
    return result.scalar_one_or_none()


async def update_announcement_channel_msg(
    session: AsyncSession, ann_id: int, channel_msg_id: int
):
    await session.execute(
        update(Announcement)
        .where(Announcement.id == ann_id)
        .values(channel_msg_id=channel_msg_id)
    )
    await session.commit()


async def update_announcement_status(
    session: AsyncSession, ann_id: int, status: str
):
    await session.execute(
        update(Announcement)
        .where(Announcement.id == ann_id)
        .values(status=status)
    )
    await session.commit()


async def update_announcement_passengers(
    session: AsyncSession, ann_id: int, count: int
):
    await session.execute(
        update(Announcement)
        .where(Announcement.id == ann_id)
        .values(passengers_count=count)
    )
    await session.commit()


async def get_expired_announcements(session: AsyncSession) -> List[Announcement]:
    cutoff = datetime.utcnow() - timedelta(hours=24)
    result = await session.execute(
        select(Announcement).where(
            and_(Announcement.status == "active", Announcement.created_at < cutoff)
        )
    )
    return result.scalars().all()


async def get_today_announcements_count(session: AsyncSession) -> int:
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count())
        .select_from(Announcement)
        .where(Announcement.created_at >= today)
    )
    return result.scalar_one()


async def get_avg_price_stats(session: AsyncSession) -> dict:
    result_nm = await session.execute(
        select(func.count()).select_from(Announcement).where(
            and_(Announcement.direction == "nukus_mangit", Announcement.status == "active")
        )
    )
    result_mn = await session.execute(
        select(func.count()).select_from(Announcement).where(
            and_(Announcement.direction == "mangit_nukus", Announcement.status == "active")
        )
    )
    return {
        "nukus_mangit": result_nm.scalar_one(),
        "mangit_nukus": result_mn.scalar_one(),
    }


# ==================== RATING QUERIES ====================

async def add_rating(
    session: AsyncSession,
    driver_id: int,
    passenger_id: int,
    score: int,
    comment: Optional[str] = None,
) -> Rating:
    rating = Rating(
        driver_id=driver_id,
        passenger_id=passenger_id,
        score=score,
        comment=comment,
    )
    session.add(rating)
    await session.commit()
    await session.refresh(rating)
    return rating


async def get_driver_avg_rating(session: AsyncSession, driver_id: int) -> Optional[float]:
    result = await session.execute(
        select(func.avg(Rating.score)).where(Rating.driver_id == driver_id)
    )
    return result.scalar_one()


async def get_driver_rating_count(session: AsyncSession, driver_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(Rating).where(Rating.driver_id == driver_id)
    )
    return result.scalar_one()


async def get_low_rating_drivers(session: AsyncSession, threshold: float = 3.0) -> list:
    result = await session.execute(
        select(Rating.driver_id, func.avg(Rating.score).label("avg_score"))
        .group_by(Rating.driver_id)
        .having(func.avg(Rating.score) < threshold)
    )
    return result.all()


async def get_complaints(session: AsyncSession) -> List[Rating]:
    result = await session.execute(
        select(Rating)
        .where(and_(Rating.score <= 2, Rating.comment.isnot(None)))
        .order_by(Rating.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


async def get_top_drivers(session: AsyncSession, limit: int = 5) -> list:
    result = await session.execute(
        select(Rating.driver_id, func.avg(Rating.score).label("avg"), func.count().label("cnt"))
        .group_by(Rating.driver_id)
        .having(func.count() >= 3)
        .order_by(func.avg(Rating.score).desc())
        .limit(limit)
    )
    return result.all()
