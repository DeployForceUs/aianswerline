# Версия 5.17 (2025-07-10)
# ✅ Подключён маршрут create_order_and_payment
# ✅ Остальной код не изменён
# ✅ Восстановлена работа /create_order_payment

import os
import json
import psycopg2
import asyncpg
import requests
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import sys

print("🟢 FastAPI v5.17 загружен успешно", flush=True)

load_dotenv(dotenv_path="/opt/aianswerline/.env")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

from addtokens import router as addtokens_router
app.include_router(addtokens_router)

from google_auth import router as google_auth_router
app.include_router(google_auth_router)

from otp_router import router as otp_router
app.include_router(otp_router)

from create_order_and_payment import router as payment_router
app.include_router(payment_router)

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
conn.autocommit = True
cur = conn.cursor()

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
            INSERT INTO users (phone, tokens_balance, created_at, email)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (From, 2, datetime.utcnow(), ''))
        user_id = cur.fetchone()[0]
        tokens = 2
        cur.execute("""
            INSERT INTO tokens_log (user_id, change, source, description, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, 2, 'system', 'Initial 2 tokens for new user', datetime.utcnow()))

    if tokens <= 0:
        phone_clean = From.lstrip("+")
        payment_url = "AIAnswerLine DOT Live" if TEST_MODE else f"https://aianswerline.live/?phone={phone_clean}"
        return f"⚠️ You have 0 tokens left. Visit: {payment_url}"

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

@app.post("/complete-registration")
async def complete_registration(phone: str = Form(...), email: str = Form(...)):
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        return JSONResponse(content={"status": "error", "message": "This email is already in use"}, status_code=400)

    cur.execute("SELECT id FROM users WHERE phone = %s", (phone,))
    row = cur.fetchone()

    if row:
        cur.execute("UPDATE users SET email = %s WHERE phone = %s", (email, phone))
        return {"status": "ok", "message": "Email linked to existing user"}
    else:
        cur.execute("""
            INSERT INTO users (phone, email, tokens_balance, created_at)
            VALUES (%s, %s, %s, %s)
        """, (phone, email, 0, datetime.utcnow()))
        return {"status": "ok", "message": "New user created with email"}

@app.post("/twilio-status")
async def twilio_status(status_data: dict):
    print("[Twilio STATUS] 📡", status_data)
    return {"status": "received"}

@app.post("/chat", response_class=PlainTextResponse)
async def chat(phone: str = Form(...), message: str = Form(...)):
    print(f"[TEST CHAT] 📲 {phone}: {message}")
    return f"Mock response to your message: {message}"

@app.post("/create-payment")
async def create_payment(request: Request):
    return {"status": "deprecated", "note": "Use /create_payment_link instead"}

@app.post("/webhook/square")
async def square_webhook(request: Request):
    try:
        print("[SQUARE] ✅ Webhook received")
        data = await request.json()
        print("📦 RAW webhook body:")
        print(json.dumps(data, indent=2))

        payment = data.get("data", {}).get("object", {}).get("payment", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        amount_cents = payment.get("amount_money", {}).get("amount", 0)
        fulfilled_at = payment.get("created_at", datetime.utcnow().isoformat())

        if not order_id:
            return {"status": "error", "message": "Missing order_id in webhook"}

        cur.execute("SELECT user_id FROM pending_payments WHERE order_id = %s", (order_id,))
        row = cur.fetchone()
        if not row:
            return {"status": "error", "message": "Unknown order_id"}

        user_id = row[0]
        tokens_to_add = (amount_cents // 100) * 20
        description = f"Payment via Square — ${amount_cents/100:.2f} | order_id: {order_id}"

        cur.execute("""
            INSERT INTO tokens_log (user_id, change, source, description, created_at)
            VALUES (%s, %s, 'square', %s, %s)
        """, (user_id, tokens_to_add, description, datetime.utcnow()))
        cur.execute("UPDATE users SET tokens_balance = tokens_balance + %s WHERE id = %s", (tokens_to_add, user_id))
        cur.execute("""
            UPDATE pending_payments
            SET fulfilled = TRUE,
                status = 'fulfilled',
                payment_id = %s,
                fulfilled_at = %s
            WHERE order_id = %s
        """, (payment_id, fulfilled_at, order_id))

        return {"status": "ok", "tokens_added": tokens_to_add}

    except Exception as e:
        print("[SQUARE ERROR]:", str(e))
        return {"status": "error", "details": f"webhook error: {str(e)}"}

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def serve_landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
