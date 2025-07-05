# Версия 1.1.1 (2025-07-05)
# Webhook listener for Square + PostgreSQL (из .env)

from fastapi import FastAPI, Request
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv('/opt/aianswerline/.env')

app = FastAPI()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}


@app.post("/webhook/square")
async def square_webhook(request: Request):
    try:
        payload = await request.json()
        event_type = payload.get("type")
        metadata = payload.get("data", {}).get("object", {}).get("payment", {}).get("metadata", {})
        phone = metadata.get("phone")

        if event_type != "payment.created" or not phone:
            return {"status": "ignored", "reason": "missing phone or unsupported event"}

        conn = await asyncpg.connect(**DB_CONFIG)
        await conn.execute("""
            INSERT INTO tokens_log (user_id, change, source, description)
            VALUES ((SELECT id FROM users WHERE phone_number = $1), 10, 'square', 'Payment detected via webhook')
        """, phone)
        await conn.close()

        return {"status": "ok", "message": "tokens added"}
    except Exception as e:
        return {"status": "error", "details": str(e)}
