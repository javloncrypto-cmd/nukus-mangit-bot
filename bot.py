import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Awaitable, Any

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, TelegramObject

from config import BOT_TOKEN, ADMIN_IDS, SUPER_ADMIN_IDS
from db.database import create_tables, async_session_maker
from handlers import common, passenger, driver, admin, super_admin
from scheduler.tasks import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    server.serve_forever()


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start",      description="Botni boshlash"),
        BotCommand(command="cancel",     description="Bekor qilish"),
        BotCommand(command="admin",      description="Admin panel"),
        BotCommand(command="superadmin", description="Super Admin panel"),
    ]
    await bot.set_my_commands(commands)


async def migrate_admins():
    """Eski ADMIN_IDS va SUPER_ADMIN_IDS ni DB ga bir marta ko'chiradi"""
    from db import queries
    async with async_session_maker() as session:
        await queries.migrate_old_admin_ids(session, ADMIN_IDS, SUPER_ADMIN_IDS)
    logger.info("Admin migratsiyasi bajarildi.")


async def main():
    logger.info("Bot ishga tushmoqda...")

    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    logger.info("Health check server port 10000 da ishga tushdi.")

    await create_tables()
    logger.info("Ma'lumotlar bazasi tayyor.")

    await migrate_admins()

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DbSessionMiddleware())

    # Routerlar tartibi muhim: super_admin → admin → common → ...
    dp.include_router(super_admin.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(passenger.router)
    dp.include_router(driver.router)

    await set_commands(bot)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler ishga tushdi.")

    logger.info("Polling boshlanmoqda...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    asyncio.run(main())
