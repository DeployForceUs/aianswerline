# Версия 1.0.1 (2025-07-05)
# Direct call to Square API without SDK — .env подключён

from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SQUARE_API_URL = "https://connect.squareup.com/v2/customers"

@app.post("/addtokens")
async def add_tokens(request: Request):
    data = await request.json()

    headers = {
        "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(SQUARE_API_URL, json=data, headers=headers)

    return {
        "status": response.status_code,
        "square_response": response.json()
    }
