import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from db.database import create_tables, async_session_maker
from handlers import common, passenger, driver, admin
from scheduler.tasks import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="cancel", description="Bekor qilish"),
        BotCommand(command="admin", description="Admin panel"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logger.info("Bot ishga tushmoqda...")

    # Create DB tables
    await create_tables()
    logger.info("Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middleware: inject DB session
    from aiogram import BaseMiddleware
    from typing import Callable, Awaitable, Any
    from aiogram.types import TelegramObject

    class DbSessionMiddleware(BaseMiddleware):
        async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
        ) -> Any:
            async with async_session_maker() as session:
                data["session"] = session
                return await handler(event, data)

    dp.update.middleware(DbSessionMiddleware())

    # Register routers
    dp.include_router(common.router)
    dp.include_router(passenger.router)
    dp.include_router(driver.router)
    dp.include_router(admin.router)

    # Set commands
    await set_commands(bot)

    # Start scheduler
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
