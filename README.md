# Nukus-Mangit Taksi Hamrohi Bot

Telegram bot — Nukus va Mangit orasida yo'lovchi va haydovchilarni bog'lash.

## Texnologiyalar
- Python 3.10+
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

### 2. Virtual muhit yaratish
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. PostgreSQL sozlash
```bash
sudo -u postgres psql
CREATE DATABASE nukus_mangit_db;
CREATE USER bot_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE nukus_mangit_db TO bot_user;
\q

psql -U bot_user -d nukus_mangit_db -f migrations.sql
```

### 5. .env fayl yaratish
```bash
cp .env.example .env
nano .env
```

`.env` faylini to'ldiring:
```
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=-100xxxxxxxxxx
ADMIN_IDS=123456789,987654321
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nukus_mangit_db
DB_USER=bot_user
DB_PASS=strong_password
```

### 6. Botni ishga tushirish
```bash
python bot.py
```

## Systemd orqali avtomatik ishga tushirish (Oracle Cloud)

```bash
sudo nano /etc/systemd/system/nukus-mangit-bot.service
```

```ini
[Unit]
Description=Nukus Mangit Taxi Bot
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/nukus_mangit_bot
ExecStart=/home/ubuntu/nukus_mangit_bot/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable nukus-mangit-bot
sudo systemctl start nukus-mangit-bot
sudo systemctl status nukus-mangit-bot
```

## Loglarni ko'rish
```bash
sudo journalctl -u nukus-mangit-bot -f
```

## Fayl tuzilmasi
```
nukus_mangit_bot/
├── bot.py                  # Asosiy kirish nuqtasi
├── config.py               # .env sozlamalari
├── requirements.txt        # Kutubxonalar
├── migrations.sql          # DB jadvallari
├── .env.example            # Namuna .env
├── handlers/
│   ├── common.py           # /start, ro'yxat, reyting
│   ├── passenger.py        # Yo'lovchi flow
│   ├── driver.py           # Haydovchi flow
│   └── admin.py            # Admin panel
├── keyboards/
│   └── keyboards.py        # Barcha tugmalar
├── db/
│   ├── database.py         # ORM modellari, ulanish
│   └── queries.py          # SQL so'rovlar
├── scheduler/
│   └── tasks.py            # APScheduler vazifalari
└── utils/
    └── templates.py        # Kanal shablonlari
```
