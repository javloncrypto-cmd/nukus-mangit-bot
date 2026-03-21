import asyncio
import logging
import os
import threading
import time
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Awaitable, Any

import aiohttp
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import BotCommand, TelegramObject, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS, SUPER_ADMIN_IDS
from db.database import create_tables, async_session_maker
from handlers import common, passenger, driver, admin, super_admin
from scheduler.tasks import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ===================== HEALTH SERVER =====================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
    def log_message(self, format, *args):
        pass

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Health server port {port} da ishga tushdi.")
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

# ===================== CONFLICT FIX =====================

async def drop_pending_updates(bot: Bot):
    """Eski instance qoldiqlarini tozalaydi — conflict oldini oladi."""
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook va pending updates tozalandi.")
    except Exception as e:
        logger.warning(f"delete_webhook xato: {e}")

# ===================== STORAGE =====================

def get_storage():
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            storage = RedisStorage.from_url(redis_url)
            logger.info("RedisStorage ulandi.")
            return storage
        except Exception as e:
            logger.warning(f"Redis ulanmadi, MemoryStorage: {e}")
    else:
        logger.warning("REDIS_URL topilmadi — MemoryStorage ishlatilmoqda.")
    return MemoryStorage()

# ===================== MIDDLEWARES =====================

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)


class AntiSpamMiddleware(BaseMiddleware):
    LIMIT = 3
    WINDOW = 1.0
    COOLDOWN = 5.0

    def __init__(self):
        self._counts = defaultdict(list)
        self._blocked = {}

    def _uid(self, event):
        if isinstance(event, (Message, CallbackQuery)):
            return event.from_user.id if event.from_user else None
        return None

    async def __call__(self, handler, event, data):
        uid = self._uid(event)
        if uid is None:
            return await handler(event, data)

        now = time.monotonic()

        if uid in self._blocked:
            if now - self._blocked[uid] < self.COOLDOWN:
                if isinstance(event, CallbackQuery):
                    await event.answer("Biroz kuting...", show_alert=False)
                return
            del self._blocked[uid]

        self._counts[uid] = [t for t in self._counts[uid] if now - t < self.WINDOW]

        if len(self._counts[uid]) >= self.LIMIT:
            self._blocked[uid] = now
            if isinstance(event, Message):
                await event.answer("Juda tez! Biroz kuting.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Juda tez!", show_alert=False)
            return

        self._counts[uid].append(now)
        return await handler(event, data)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception(f"Handler xato: {e}")
            try:
                if isinstance(event, Message):
                    await event.answer("Xato yuz berdi. Qayta urining.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Xato yuz berdi.", show_alert=True)
            except Exception:
                pass

# ===================== SETUP =====================

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start",      description="Botni boshlash"),
        BotCommand(command="cancel",     description="Bekor qilish"),
        BotCommand(command="admin",      description="Admin panel"),
        BotCommand(command="superadmin", description="Super Admin panel"),
    ]
    await bot.set_my_commands(commands)


async def migrate_admins():
    from db import queries
    async with async_session_maker() as session:
        await queries.migrate_old_admin_ids(session, ADMIN_IDS, SUPER_ADMIN_IDS)
    logger.info("Admin migratsiyasi bajarildi.")

# ===================== MAIN =====================

async def main():
    logger.info("Bot ishga tushmoqda...")

    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

    # DB ulanish — 5 marta urinish
    for attempt in range(1, 6):
        try:
            logger.info(f"DB ulanish {attempt}/5...")
            await create_tables()
            logger.info("DB tayyor.")
            break
        except Exception as e:
            logger.error(f"DB xato ({attempt}/5): {e}")
            if attempt == 5:
                raise
            await asyncio.sleep(5)

    try:
        await migrate_admins()
    except Exception as e:
        logger.warning(f"Migratsiya xato (davom etiladi): {e}")

    bot = Bot(token=BOT_TOKEN)

    # Conflict oldini olish: webhook o'chir + eski so'rovlarni tozala
    await drop_pending_updates(bot)
    # Eski instance to'liq o'lishi uchun 2 soniya kutish
    await asyncio.sleep(2)

    storage = get_storage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(ErrorMiddleware())
    dp.update.middleware(AntiSpamMiddleware())
    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(super_admin.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(passenger.router)
    dp.include_router(driver.router)

    try:
        await set_commands(bot)
    except Exception as e:
        logger.warning(f"set_commands xato: {e}")

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler ishga tushdi. Polling boshlanmoqda...")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,  # har restart'da eski xabarlarni o'tkazib yubor
        )
    finally:
        scheduler.shutdown()
        await bot.session.close()
        if hasattr(storage, "close"):
            await storage.close()
        logger.info("Bot toxtatildi.")


if __name__ == "__main__":
    asyncio.run(main())
