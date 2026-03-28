# Nukus-Mangit Taksi Hamrohi Bot

Telegram bot — Nukus va Mangit orasida yo'lovchilarni bog'lash.

## Versiyalar

| Versiya | Holat | Tavsif |
|---------|-------|--------|
| **V1** (hozirgi) | ✅ Faol | Faqat yo'lovchi e'lonlari |
| V2 (kelajak) | 🔜 Rejalashtirilgan | Haydovchi e'lonlari + reyting |

## Texnologiyalar
- Python 3.11
- Aiogram 3.x (async)
- PostgreSQL 14+
- SQLAlchemy 2.0 (async)
- APScheduler 3.x


## O'rnatish

### 1. Reponi klonlash
```bash
git clone <repo-url>
cd nukus_mangit_bot
```

### 2. Virtual muhit va kutubxonalar
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. PostgreSQL sozlash
```bash
sudo -u postgres psql
CREATE DATABASE nukus_mangit_db;
CREATE USER bot_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE nukus_mangit_db TO bot_user;
\q

psql -U bot_user -d nukus_mangit_db -f migrations.sql
```

### 4. .env fayl
```bash
cp .env.example .env
nano .env
```

### 5. Ishga tushirish
```bash
python bot.py
```

## V2 ga o'tish (haydovchi qo'shish)

1. `config.py` da `DRIVER_MODE = True` qiling
2. `bot.py` da haydovchi handler ni yoching:
   ```python
   from handlers import driver
   dp.include_router(driver.router)
   ```
3. `keyboards/keyboards.py` da V2 tugmalarini yoching
4. `utils/templates.py` da `driver_announcement_text` ni yoching
5. `scheduler/tasks.py` da haydovchi vazifalarini yoching
6. `main_menu_kb()` funksiyasiga haydovchi tugmalarini qo'shing
