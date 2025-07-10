# Версия 2.0 (2025-07-09)
# ✅ Обновлён для работы с таблицей pending_payments

import json
from fastapi import Request
from fastapi.routing import APIRouter
import psycopg2
from datetime import datetime
import os

router = APIRouter()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
conn.autocommit = True
cur = conn.cursor()

@router.post("/webhook/square")
async def square_webhook(request: Request):
    try:
        print("[SQUARE] ✅ Webhook received")

        data = await request.json()
        print("📦 RAW webhook body:")
        print(json.dumps(data, indent=2))

        payment = data.get("data", {}).get("object", {}).get("payment", {})
        metadata = payment.get("metadata", {})
        amount_cents = payment.get("amount_money", {}).get("amount", 0)
        payment_id = payment.get("id", "UNKNOWN")
        order_id = metadata.get("order_id")
        phone = metadata.get("phone")

        if order_id and amount_cents > 0:
            cur.execute("""
                UPDATE pending_payments
                SET fulfilled = true,
                    fulfilled_at = %s,
                    payment_id = %s,
                    status = 'paid'
                WHERE order_id = %s
            """, (datetime.utcnow(), payment_id, order_id))
            return {"status": "ok", "message": "pending_payment updated"}

        return {"status": "ok", "message": "webhook received, no order_id or invalid amount"}

    except Exception as e:
        print("[SQUARE ERROR]:", str(e))
        return {"status": "error", "details": f"webhook error: {str(e)}"}
