import os
import asyncio
from webhook import app

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
```

Saqlang.

---

## 5. requirements.txt ni yangilang

`requirements.txt` faylini oching va quyidagicha o'zgartiring:
```
aiogram==3.7.0
asyncpg==0.29.0
SQLAlchemy==2.0.30
apscheduler==3.10.4
python-dotenv==1.0.1
aiosqlite==0.20.0
flask==3.0.3
waitress==3.0.0