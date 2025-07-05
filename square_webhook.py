# Версия 1.0.0 (2025-07-04)
# Webhook handler for Square payment events

from fastapi import FastAPI, Request
import os
import httpx
from dotenv import load_dotenv

load_dotenv('/opt/aianswerline/.env')

app = FastAPI()

SQUARE_SECRET = os.getenv("SQUARE_ACCESS_TOKEN")

@app.post("/webhook/square")
async def handle_webhook(request: Request):
    payload = await request.json()
    phone = payload.get("data", {}).get("object", {}).get("payment", {}).get("metadata", {}).get("phone")

    if not phone:
        return {"status": "error", "message": "phone not found in metadata"}

    # Имитация начисления токенов
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8000/addtokens", json={"phone_number": phone})

    return {"status": "ok", "message": "tokens added"}
