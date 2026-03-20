import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "0"))
ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",")]

DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
DB_NAME: str = os.getenv("DB_NAME", "nukus_mangit_db")
DB_USER: str = os.getenv("DB_USER", "bot_user")
DB_PASS: str = os.getenv("DB_PASS", "")

DATABASE_URL: str = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
