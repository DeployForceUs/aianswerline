# Версия 1.7 (2025-07-09)
# ✅ Расширенная вставка в pending_payments со всеми ключевыми полями
# ✅ Запись полной square_response
# ✅ Логгирование всех этапов

import os
import uuid
import json
import httpx
import psycopg2
import logging
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

router = APIRouter()

SQUARE_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SQUARE_LOCATION = os.getenv("SQUARE_LOCATION_ID")

DB_HOST = "172.18.0.2"
DB_NAME = "twiliogateway"
DB_USER = "twilio"
DB_PASS = os.getenv("POSTGRES_PASSWORD")

@router.get("/create_payment_link")
async def create_payment_link(amount: int, phone: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://connect.squareup.com/v2/online-checkout/payment-links",
            headers={
                "Authorization": f"Bearer {SQUARE_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "idempotency_key": str(uuid.uuid4()),
                "quick_pay": {
                    "name": "Token Recharge",
                    "price_money": {
                        "amount": amount * 100,
                        "currency": "USD"
                    },
                    "location_id": SQUARE_LOCATION
                },
                "checkout_options": {
                    "redirect_url": "https://aianswerline.live"
                },
                "metadata": {
                    "phone": phone
                }
            }
        )

        data = response.json()
        url = data["payment_link"]["url"]
        order_id = data["payment_link"]["id"]
        square_response = json.dumps(data)
        metadata = json.dumps({"phone": phone})

        logging.info(f"📌 Вставка в pending_payments: phone={phone}, amount={amount}, url={url}, order_id={order_id}")

        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO pending_payments (
                    user_id, email, phone, order_id, payment_id,
                    payment_link, amount, currency, status, fulfilled,
                    metadata, square_response, created_at, fulfilled_at
                )
                VALUES (
                    NULL, NULL, %s, %s, NULL,
                    %s, %s, 'USD', 'pending', false,
                    %s, %s, %s, NULL
                )
            """, (
                phone, order_id, url, amount,
                metadata, square_response, datetime.utcnow()
            ))
            conn.commit()
            cur.close()
            conn.close()
            logging.info("✅ Вставка прошла успешно.")
        except Exception as e:
            logging.error(f"❌ Ошибка вставки в pending_payments: {e}")

        return RedirectResponse(url)
