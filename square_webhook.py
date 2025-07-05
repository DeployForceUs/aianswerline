# Версия 1.1.0 (2025-07-05)
# Принимаем Square Webhook, парсим номер, начисляем токены в Postgres

from fastapi import APIRouter, Request
import asyncpg
import os
import logging

router = APIRouter()

DB_URL = os.getenv("DATABASE_URL")  # пример: postgres://user:pass@host:port/db

@router.post("/square-webhook")
async def square_webhook(request: Request):
    try:
        payload = await request.json()
        logging.info(f"Square Webhook payload: {payload}")

        # ⚠️ Тут подставь путь к номеру телефона — если custom_field, то так:
        phone_number = payload.get("data", {}).get("object", {}).get("payment", {}).get("note", "")
        amount_money = payload.get("data", {}).get("object", {}).get("payment", {}).get("amount_money", {}).get("amount", 0)

        if not phone_number:
            return {"error": "No phone number found in webhook"}

        # 💰 Определяем, сколько токенов зачислить (доллары -> токены)
        tokens_to_add = int(amount_money) // 100  # допустим 1 доллар = 1 токен

        conn = await asyncpg.connect(DB_URL)

        # Проверка — есть ли такой пользователь
        user = await conn.fetchrow("SELECT id FROM users WHERE phone_number = $1", phone_number)
        if not user:
            await conn.close()
            return {"error": f"User with phone {phone_number} not found"}

        user_id = user["id"]

        # Зачисляем токены
        await conn.execute(
            "INSERT INTO tokens_log (user_id, change, source, description) VALUES ($1, $2, $3, $4)",
            user_id, tokens_to_add, "square", f"Payment received via Square"
        )

        await conn.close()
        return {"status": "ok", "tokens_added": tokens_to_add}

    except Exception as e:
        logging.exception("Error processing Square webhook")
        return {"error": str(e)}
