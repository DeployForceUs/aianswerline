# Версия 5.3 (2025-07-08)
# ✅ description теперь включает и phone, и payment_id
# ✅ Поле phone используется везде, phone_number удалён

import os
import json
import psycopg2
import asyncpg
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from openai import OpenAI

load_dotenv(dotenv_path="/opt/aianswerline/.env")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# === Роутеры ===
from addtokens import router as addtokens_router
app.include_router(addtokens_router)  # убрали префикс /addtokens

from google_auth import router as google_auth_router
app.include_router(google_auth_router)

from otp_router import router as otp_router
app.include_router(otp_router)

from create_order_and_payment import router as payment_router
app.include_router(payment_router)

# === Sync DB (psycopg2) ===
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
conn.autocommit = True
cur = conn.cursor()

# === Async DB (asyncpg) ===
@app.on_event("startup")
async def startup():
    app.state.pg_pool = await asyncpg.create_pool(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        min_size=1,
        max_size=5
    )

# === OpenAI ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/twilio-hook", response_class=PlainTextResponse)
async def twilio_hook(From: str = Form(...), Body: str = Form(...)):
    print(f"[Twilio SMS] 📩 From {From}: {Body}")
    cur.execute("SELECT id, tokens_balance FROM users WHERE phone = %s", (From,))
    row = cur.fetchone()

    if row:
        user_id, tokens = row
    else:
        cur.execute("""
            INSERT INTO users (phone, verification_code, is_verified, tokens_balance, created_at)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (From, '000000', True, 2, datetime.utcnow()))
        user_id = cur.fetchone()[0]
        tokens = 2
        cur.execute("""
            INSERT INTO tokens_log (user_id, change, source, description, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, 2, 'system', 'Initial 2 tokens for new user', datetime.utcnow()))

    if tokens <= 0:
        phone_clean = From.lstrip("+")
        payment_url = f"https://aianswerline.live/addtokens/{phone_clean}"
        return f"⚠️ You've run out of tokens.\nBuy more here:\n{payment_url}"

    cur.execute("UPDATE users SET tokens_balance = tokens_balance - 1 WHERE id = %s", (user_id,))
    cur.execute("""
        INSERT INTO tokens_log (user_id, change, source, description, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, -1, 'chat', f"Message: {Body[:50]}", datetime.utcnow()))

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": Body}
            ]
        )
        gpt_response = completion.choices[0].message.content.strip()
    except Exception as e:
        print("[OpenAI ERROR]:", e)
        gpt_response = "Sorry, there was an error generating a response."

    return gpt_response

@app.post("/twilio-status")
async def twilio_status(status_data: dict):
    print("[Twilio STATUS] 📡", status_data)
    return {"status": "received"}

@app.post("/chat", response_class=PlainTextResponse)
async def chat(phone: str = Form(...), message: str = Form(...)):
    print(f"[TEST CHAT] 📲 {phone}: {message}")
    return f"Mock response to your message: {message}"

@app.post("/webhook/square")
async def square_webhook(request: Request):
    try:
        data = await request.json()
        print("[SQUARE] ✅ Webhook received")

        dump_dir = Path("/opt/aianswerline/tmp")
        dump_dir.mkdir(parents=True, exist_ok=True)
        dump_path = dump_dir / "square_webhook_dump.json"
        with open(dump_path, "a") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        payment = data.get("data", {}).get("object", {}).get("payment", {})
        metadata = payment.get("metadata", {})
        amount_cents = payment.get("amount_money", {}).get("amount", 0)
        phone = metadata.get("phone")
        payment_id = payment.get("id", "UNKNOWN")

        if phone and amount_cents > 0:
            tokens_to_add = (amount_cents // 100) * 20
            cur.execute("SELECT id FROM users WHERE phone = %s", (phone,))
            row = cur.fetchone()
            if row:
                user_id = row[0]
                description = f"Payment received: ${amount_cents/100:.2f} | Phone: {phone} | ID: {payment_id}"
                cur.execute("""
                    INSERT INTO tokens_log (user_id, change, source, description, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, tokens_to_add, 'square', description, datetime.utcnow()))
                cur.execute("UPDATE users SET tokens_balance = tokens_balance + %s WHERE id = %s", (tokens_to_add, user_id))
                return {"status": "ok", "message": f"{tokens_to_add} tokens added"}

        return {"status": "ok", "message": "webhook received, no phone or amount invalid"}

    except Exception as e:
        return {"status": "error", "details": f"webhook error: {str(e)}"}

# === Landing Page ===
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def serve_landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
