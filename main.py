# Версия 3.8 (2025-07-05)
# ✅ XML отключён, только текст
# ✅ Добавлена персональная ссылка на оплату по номеру: /addtokens/{номер}
# ✅ Подключено по фэншую через include_router
# ✅ Всё остальное без изменений

import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

load_dotenv(dotenv_path="/opt/aianswerline/.env")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# === Подключение /addtokens по фэншую ===
from addtokens import router as addtokens_router
app.include_router(addtokens_router, prefix="/addtokens")

# === DB Connect ===
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
conn.autocommit = True
cur = conn.cursor()

# === OpenAI ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/twilio-hook", response_class=PlainTextResponse)
async def twilio_hook(From: str = Form(...), Body: str = Form(...)):
    print(f"[Twilio SMS] 📩 From {From}: {Body}")

    cur.execute("SELECT id, tokens_balance FROM users WHERE phone_number = %s", (From,))
    row = cur.fetchone()

    if row:
        user_id, tokens = row
    else:
        cur.execute("""
            INSERT INTO users (phone_number, verification_code, is_verified, tokens_balance, created_at)
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
async def chat(phone_number: str = Form(...), message: str = Form(...)):
    print(f"[TEST CHAT] 📲 {phone_number}: {message}")
    return f"Mock response to your message: {message}"
