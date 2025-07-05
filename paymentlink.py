# paymentlink.py
# Версия 1.0 (2025-07-05)
# Генерирует ссылку на оплату через Square, с привязкой к номеру телефона

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
import os
from dotenv import load_dotenv

load_dotenv('/opt/aianswerline/.env')

SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SQUARE_API_URL = "https://connect.squareup.com/v2/online-checkout/payment-links"

app = FastAPI()

@app.get("/paymentlink")
async def generate_payment_link(phone: str):
    headers = {
        "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    body = {
        "idempotency_key": phone.replace("+", "") + "-checkout",
        "quick_pay": {
            "name": "Top-up Chat Tokens",
            "price_money": {
                "amount": 100,   # в центах: 100 = $1.00
                "currency": "USD"
            },
            "location_id": "A6VFNGKKYHZXN"
        },
        "metadata": {
            "phone": phone
        }
    }

    try:
        resp = requests.post(SQUARE_API_URL, headers=headers, json=body)
        if resp.status_code == 200:
            data = resp.json()
            return {"status": "ok", "url": data["payment_link"]["url"]}
        else:
            return JSONResponse(status_code=resp.status_code, content={"status": "error", "details": resp.text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "details": str(e)})
