# Версия 1.0 (2025-07-07)
# ✅ Создание ссылки Square с суммой и телефоном в metadata

import os
import httpx
from fastapi import APIRouter, Request
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
                "idempotency_key": phone + str(amount),
                "quick_pay": {
                    "name": "Token Recharge",
                    "price_money": {
                        "amount": amount,
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
