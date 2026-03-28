from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, Boolean, SmallInteger, Float, Text, ForeignKey, DateTime
from datetime import datetime
from typing import Optional, List
from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # V1: role faqat 'passenger' | None
    # V2 (kelajak): 'driver' roli qo'shiladi
    role: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    announcements: Mapped[List["Announcement"]] = relationship(back_populates="user")
    admin_record: Mapped[Optional["Admin"]] = relationship(
        back_populates="user", foreign_keys="Admin.user_id", uselist=False
    )


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), unique=True)
    role: Mapped[str] = mapped_column(String(20), default="admin")  # 'super_admin' | 'admin'
    added_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="admin_record", foreign_keys=[user_id])


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    direction: Mapped[str] = mapped_column(String(20))  # 'nukus_mangit' | 'mangit_nukus'
    passengers_count: Mapped[int] = mapped_column(SmallInteger)
    price: Mapped[str] = mapped_column(String(50))
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    channel_msg_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # V1 statuslar: 'active' | 'completed' | 'expired'
    status: Mapped[str] = mapped_column(String(20), default="active")
    # V1: ann_type faqat 'passenger'
    # V2 (kelajak): 'driver' qo'shiladi
    ann_type: Mapped[str] = mapped_column(String(20), default="passenger")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="announcements")


# V2 (kelajak): Rating modeli haydovchilar uchun kerak bo'ladi
class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    driver_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    passenger_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    score: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BotSetting(Base):
    __tablename__ = "bot_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    against_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    ann_id: Mapped[Optional[int]] = mapped_column(ForeignKey("announcements.id"), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | reviewed | closed
    reviewed_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=10, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
