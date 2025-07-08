# Версия 1.4 (2025-07-08)
# ✅ Square требует {"order_id": ...} — окончательно исправлено!
# ✅ Прямой Redirect после успешной генерации ссылки
# ✅ Добавлена отладочная печать SQUARE_LOCATION и TOKEN в журнал

from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import APIRouter
import os
import uuid
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path="/opt/aianswerline/.env")

router = APIRouter()

SQUARE_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SQUARE_LOCATION = os.getenv("SQUARE_LOCATION_ID")

print(f"🔍 SQUARE_LOCATION = {SQUARE_LOCATION}")
print(f"🔍 SQUARE_TOKEN    = {SQUARE_TOKEN[:8]}... (trimmed)")

@router.get("/create_order_payment")
async def create_order_payment(amount: int, phone: str):
    order_idempotency_key = str(uuid.uuid4())
    payment_idempotency_key = f"{phone}-{amount}-{uuid.uuid4().hex[:6]}"

    headers = {
        "Authorization": f"Bearer {SQUARE_TOKEN}",
        "Content-Type": "application/json"
    }

    order_payload = {
        "idempotency_key": order_idempotency_key,
        "order": {
            "location_id": SQUARE_LOCATION,
            "line_items": [
                {
                    "name": "Token Purchase",
                    "quantity": "1",
                    "base_price_money": {
                        "amount": amount * 100,
                        "currency": "USD"
                    }
                }
            ],
            "metadata": {
                "phone": phone
            }
        }
    }

    async with httpx.AsyncClient() as client:
        order_resp = await client.post(
            "https://connect.squareup.com/v2/orders",
            headers=headers,
            json=order_payload
        )
        order_data = order_resp.json()
        if order_resp.status_code != 200 or "order" not in order_data:
            return JSONResponse({
                "error": "Order creation failed",
                "raw": order_data
            }, status_code=500)

        order_id = order_data["order"]["id"]

        payment_payload = {
            "idempotency_key": payment_idempotency_key,
            "order_id": order_id,
            "checkout_options": {
                "redirect_url": "https://aianswerline.live"
            }
        }

        payment_resp = await client.post(
            "https://connect.squareup.com/v2/online-checkout/payment-links",
            headers=headers,
            json=payment_payload
        )

        payment_data = payment_resp.json()
        if payment_resp.status_code != 200 or "payment_link" not in payment_data:
            return JSONResponse({
                "error": "No payment link returned",
                "raw": payment_data
            }, status_code=500)

        url = payment_data["payment_link"]["url"]
        return RedirectResponse(url)
