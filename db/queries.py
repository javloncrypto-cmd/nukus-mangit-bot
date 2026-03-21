from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List
from db.database import User, Announcement, Rating, Admin, BotSetting, SystemLog, Complaint
from datetime import datetime, timedelta


# ==================== USER ====================

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
    await session.execute(update(User).where(User.user_id == user_id).values(phone=phone))
    await session.commit()


async def update_user_role(session: AsyncSession, user_id: int, role: str):
    await session.execute(update(User).where(User.user_id == user_id).values(role=role))
    await session.commit()


async def update_user_name(session: AsyncSession, user_id: int, full_name: str):
    await session.execute(update(User).where(User.user_id == user_id).values(full_name=full_name))
    await session.commit()


async def ban_user(session: AsyncSession, user_id: int, is_banned: bool = True):
    await session.execute(update(User).where(User.user_id == user_id).values(is_banned=is_banned))
    await session.commit()


async def get_all_users_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def search_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    return await get_user(session, user_id)


async def get_all_users(session: AsyncSession, offset: int = 0, limit: int = 20) -> List[User]:
    result = await session.execute(
        select(User).order_by(desc(User.created_at)).offset(offset).limit(limit)
    )
    return result.scalars().all()


# ==================== ADMIN ====================

async def get_admin(session: AsyncSession, user_id: int) -> Optional[Admin]:
    result = await session.execute(
        select(Admin).where(and_(Admin.user_id == user_id, Admin.is_active == True))
    )
    return result.scalar_one_or_none()


async def get_admin_role(session: AsyncSession, user_id: int) -> Optional[str]:
    """Foydalanuvchi admin rolini qaytaradi: 'super_admin', 'admin' yoki None"""
    admin = await get_admin(session, user_id)
    return admin.role if admin else None


async def is_super_admin(session: AsyncSession, user_id: int) -> bool:
    from config import SUPER_ADMIN_IDS
    if user_id in SUPER_ADMIN_IDS:
        return True
    admin = await get_admin(session, user_id)
    return admin is not None and admin.role == "super_admin"


async def is_admin_or_super(session: AsyncSession, user_id: int) -> bool:
    from config import SUPER_ADMIN_IDS
    if user_id in SUPER_ADMIN_IDS:
        return True
    admin = await get_admin(session, user_id)
    return admin is not None and admin.is_active


async def add_admin(session: AsyncSession, user_id: int, role: str, added_by: int) -> Admin:
    existing = await get_admin(session, user_id)
    if existing:
        existing.role = role
        existing.is_active = True
        await session.commit()
        return existing
    admin = Admin(user_id=user_id, role=role, added_by=added_by)
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


async def remove_admin(session: AsyncSession, user_id: int):
    await session.execute(
        update(Admin).where(Admin.user_id == user_id).values(is_active=False)
    )
    await session.commit()


async def get_all_admins(session: AsyncSession) -> List[Admin]:
    result = await session.execute(
        select(Admin).options(selectinload(Admin.user)).where(Admin.is_active == True)
    )
    return result.scalars().all()


async def migrate_old_admin_ids(session: AsyncSession, admin_ids: list, super_admin_ids: list):
    """Eski ADMIN_IDS ni DB ga ko'chiradi — bir marta ishlatiladi"""
    for uid in super_admin_ids:
        user = await get_user(session, uid)
        if user:
            await add_admin(session, uid, "super_admin", uid)
    for uid in admin_ids:
        if uid not in super_admin_ids:
            user = await get_user(session, uid)
            if user:
                await add_admin(session, uid, "admin", uid)


# ==================== BOT SETTINGS ====================

async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    result = await session.execute(select(BotSetting).where(BotSetting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_setting(session: AsyncSession, key: str, value: str, updated_by: int):
    result = await session.execute(select(BotSetting).where(BotSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
        setting.updated_by = updated_by
        setting.updated_at = datetime.utcnow()
    else:
        session.add(BotSetting(key=key, value=value, updated_by=updated_by))
    await session.commit()


async def get_all_settings(session: AsyncSession) -> List[BotSetting]:
    result = await session.execute(select(BotSetting).order_by(BotSetting.key))
    return result.scalars().all()


# ==================== SYSTEM LOGS ====================

async def add_log(session: AsyncSession, user_id: Optional[int], action: str, details: Optional[str] = None):
    log = SystemLog(user_id=user_id, action=action, details=details)
    session.add(log)
    await session.commit()


async def get_recent_logs(session: AsyncSession, limit: int = 50) -> List[SystemLog]:
    result = await session.execute(
        select(SystemLog).order_by(desc(SystemLog.created_at)).limit(limit)
    )
    return result.scalars().all()


async def get_logs_by_user(session: AsyncSession, user_id: int, limit: int = 20) -> List[SystemLog]:
    result = await session.execute(
        select(SystemLog)
        .where(SystemLog.user_id == user_id)
        .order_by(desc(SystemLog.created_at))
        .limit(limit)
    )
    return result.scalars().all()


# ==================== ANNOUNCEMENTS ====================

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
        select(Announcement).options(selectinload(Announcement.user)).where(Announcement.id == ann_id)
    )
    return result.scalar_one_or_none()


async def get_active_announcement_by_user(session: AsyncSession, user_id: int) -> Optional[Announcement]:
    result = await session.execute(
        select(Announcement).where(
            and_(Announcement.user_id == user_id, Announcement.status == "active")
        )
    )
    return result.scalar_one_or_none()


async def get_user_announcements(session: AsyncSession, user_id: int, limit: int = 10) -> List[Announcement]:
    result = await session.execute(
        select(Announcement)
        .where(Announcement.user_id == user_id)
        .order_by(desc(Announcement.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def get_all_active_announcements(session: AsyncSession) -> List[Announcement]:
    result = await session.execute(
        select(Announcement)
        .options(selectinload(Announcement.user))
        .where(Announcement.status == "active")
        .order_by(desc(Announcement.created_at))
    )
    return result.scalars().all()


async def update_announcement_channel_msg(session: AsyncSession, ann_id: int, channel_msg_id: int):
    await session.execute(
        update(Announcement).where(Announcement.id == ann_id).values(channel_msg_id=channel_msg_id)
    )
    await session.commit()


async def update_announcement_status(session: AsyncSession, ann_id: int, status: str):
    await session.execute(
        update(Announcement).where(Announcement.id == ann_id).values(status=status)
    )
    await session.commit()


async def update_announcement_passengers(session: AsyncSession, ann_id: int, count: int):
    await session.execute(
        update(Announcement).where(Announcement.id == ann_id).values(passengers_count=count)
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
        select(func.count()).select_from(Announcement).where(Announcement.created_at >= today)
    )
    return result.scalar_one()


async def get_avg_price_stats(session: AsyncSession) -> dict:
    r_nm = await session.execute(
        select(func.count()).select_from(Announcement).where(
            and_(Announcement.direction == "nukus_mangit", Announcement.status == "active")
        )
    )
    r_mn = await session.execute(
        select(func.count()).select_from(Announcement).where(
            and_(Announcement.direction == "mangit_nukus", Announcement.status == "active")
        )
    )
    return {"nukus_mangit": r_nm.scalar_one(), "mangit_nukus": r_mn.scalar_one()}


# ==================== RATINGS ====================

async def add_rating(
    session: AsyncSession,
    driver_id: int,
    passenger_id: int,
    score: int,
    comment: Optional[str] = None,
) -> Rating:
    rating = Rating(driver_id=driver_id, passenger_id=passenger_id, score=score, comment=comment)
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


async def get_complaints_ratings(session: AsyncSession) -> List[Rating]:
    result = await session.execute(
        select(Rating)
        .where(and_(Rating.score <= 2, Rating.comment.isnot(None)))
        .order_by(desc(Rating.created_at))
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


# ==================== COMPLAINTS ====================

async def create_complaint(
    session: AsyncSession,
    from_user_id: int,
    against_user_id: int,
    text: str,
    ann_id: Optional[int] = None,
) -> Complaint:
    complaint = Complaint(
        from_user_id=from_user_id,
        against_user_id=against_user_id,
        text=text,
        ann_id=ann_id,
    )
    session.add(complaint)
    await session.commit()
    await session.refresh(complaint)
    return complaint


async def get_open_complaints(session: AsyncSession) -> List[Complaint]:
    result = await session.execute(
        select(Complaint).where(Complaint.status == "open").order_by(desc(Complaint.created_at))
    )
    return result.scalars().all()


async def close_complaint(session: AsyncSession, complaint_id: int, reviewed_by: int):
    await session.execute(
        update(Complaint)
        .where(Complaint.id == complaint_id)
        .values(status="closed", reviewed_by=reviewed_by)
    )
    await session.commit()
