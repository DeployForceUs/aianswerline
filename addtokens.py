# Версия 1.4 (2025-07-07)
# ✅ Исправлено кеширование Square: теперь каждый платеж уникален

import os
import uuid
import httpx
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

SQUARE_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SQUARE_LOCATION = os.getenv("SQUARE_LOCATION_ID")

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
                "idempotency_key": str(uuid.uuid4()),  # 💣 Уникальный ключ = всегда новая ссылка
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
        return RedirectResponse(url)
