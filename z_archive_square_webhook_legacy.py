# Версия 1.1.2 (2025-07-05)
# Webhook Square -> проверка, запись в Postgres + лог в файл

from fastapi import FastAPI, Request
import asyncpg
import os
import json
from dotenv import load_dotenv

load_dotenv("/opt/aianswerline/.env")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

app = FastAPI()

@app.post("/webhook/square")
async def webhook_square(request: Request):
    try:
        payload = await request.json()

        # 🪵 Запись в рабочую директорию (а не в /tmp)
        os.makedirs("/opt/aianswerline/tmp", exist_ok=True)
        with open("/opt/aianswerline/tmp/square_webhook_dump.json", "w") as f:
            json.dump(payload, f, indent=2)

        phone = payload["data"]["object"]["payment"]["metadata"].get("phone")

        if not phone:
            return {"status": "error", "details": "No phone number in metadata"}

        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )

        user = await conn.fetchrow("SELECT id FROM users WHERE phone_number = $1", phone)
        if user:
            user_id = user["id"]
        else:
            user = await conn.fetchrow(
                "INSERT INTO users (phone_number, tokens) VALUES ($1, 0) RETURNING id",
                phone
            )
            user_id = user["id"]

        await conn.execute("""
            INSERT INTO tokens_log (user_id, change, source, description)
            VALUES ($1, 1, 'square', $2)
        """, user_id, f"Top-up via Square for {phone}")

        await conn.execute("""
            UPDATE users SET tokens = tokens + 1 WHERE id = $1
        """, user_id)

        await conn.close()
        return {"status": "ok", "message": "tokens added"}

    except Exception as e:
        return {"status": "error", "details": f"DB error: {str(e)}"}
