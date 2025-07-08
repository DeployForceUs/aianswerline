# Версия 1.3.0 (2025-07-08)
# ✅ Начисляется 20 токенов за каждый доллар (из суммы платежа)
# ✅ Поддержка phone из metadata
# ✅ Запись в tokens_log и users.tokens
# ✅ Логирование webhook'а в файл
# ✅ Добавлен reference_id и payment_id в описание

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

        # 🪵 Лог в файл
        os.makedirs("/opt/aianswerline/tmp", exist_ok=True)
        with open("/opt/aianswerline/tmp/square_webhook_dump.json", "w") as f:
            json.dump(payload, f, indent=2)

        payment = payload["data"]["object"]["payment"]
        phone = payment["metadata"].get("phone")
        amount_cents = payment["amount_money"]["amount"]
        payment_id = payment["id"]
        reference_id = payment.get("reference_id", "")

        if not phone:
            return {"status": "error", "details": "No phone in metadata"}

        tokens_to_add = round((amount_cents / 100) * 20)

        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )

        user = await conn.fetchrow("SELECT id FROM users WHERE phone = $1", phone)
        if user:
            user_id = user["id"]
        else:
            user = await conn.fetchrow(
                "INSERT INTO users (phone, tokens_balance) VALUES ($1, 0) RETURNING id",
                phone
            )
            user_id = user["id"]

        description = f"Top-up via Square (ID: {payment_id}) for {phone}"
        if reference_id:
            description += f" | Ref: {reference_id}"

        await conn.execute("""
            INSERT INTO tokens_log (user_id, change, source, description)
            VALUES ($1, $2, 'square', $3)
        """, user_id, tokens_to_add, description)

        await conn.execute("""
            UPDATE users SET tokens_balance = tokens_balance + $1 WHERE id = $2
        """, tokens_to_add, user_id)

        await conn.close()
        return {"status": "ok", "tokens_added": tokens_to_add}

    except Exception as e:
        return {"status": "error", "details": f"DB error: {str(e)}"}
