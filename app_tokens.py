# Версия 2.0 (2025-07-02)
# ✅ Поддержка авторизации по номеру
# ✅ Подключение к PostgreSQL базе twilio
# ✅ Выдача стартовых токенов
# ✅ Списание токена за каждый запрос
# ✅ Ответ через Twilio SMS
# ✅ Ссылка на оплату при 0 токенов
# ✅ Добавлен тестовый endpoint /chat для локальной проверки

import os
import psycopg2
from flask import Flask, request, Response
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from datetime import datetime

# === Загрузка .env ===
load_dotenv(dotenv_path="/var/www/aianswerline/api/.env")

# === Подключение к OpenAI ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Подключение к PostgreSQL ===
conn = psycopg2.connect(
    dbname="twilio",
    user="twilio",
    password="SuperSecret",
    host="172.18.0.2",
    port="5432"
)
conn.autocommit = True
cur = conn.cursor()

# === Flask ===
app = Flask(__name__)

@app.route("/twilio-hook", methods=["POST"])
def twilio_hook():
    from_number = request.form.get("From")
    body = request.form.get("Body")

    print(f"[Twilio SMS] 📩 From {from_number}: {body}")

    # === Проверка пользователя ===
    cur.execute("SELECT id, tokens_balance FROM users WHERE phone_number = %s", (from_number,))
    row = cur.fetchone()

    if row:
        user_id, tokens = row
    else:
        # Новый пользователь → регистрируем
        cur.execute("""
            INSERT INTO users (phone_number, verification_code, is_verified, tokens_balance, created_at)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (from_number, '000000', True, 2, datetime.utcnow()))
        user_id = cur.fetchone()[0]
        tokens = 2
        cur.execute("""
            INSERT INTO tokens_log (user_id, change, source, description, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, 2, 'system', 'Initial 2 tokens for new user', datetime.utcnow()))

    # === Если токенов нет ===
    if tokens <= 0:
        response = MessagingResponse()
        response.message("⚠️ You've run out of tokens.\nBuy more here:\nhttps://yourdomain.com/pay")
        return Response(str(response), mimetype="application/xml")

    # === Списание токена ===
    cur.execute("""
        UPDATE users SET tokens_balance = tokens_balance - 1 WHERE id = %s
    """, (user_id,))
    cur.execute("""
        INSERT INTO tokens_log (user_id, change, source, description, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, -1, 'chat', f"Message: {body[:50]}", datetime.utcnow()))

    # === GPT-4 Обработка ===
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": body}
            ]
        )
        gpt_response = completion.choices[0].message.content.strip()
    except Exception as e:
        print("[OpenAI ERROR]:", e)
        gpt_response = "Sorry, there was an error generating a response."

    # === Ответ Twilio ===
    response = MessagingResponse()
    response.message(gpt_response)
    return Response(str(response), mimetype="application/xml")

@app.route("/twilio-status", methods=["POST"])
def twilio_status():
    print("[Twilio STATUS] 📡", request.form.to_dict())
    return ('', 204)

# === Тестовый эндпоинт для локального curl ===
@app.route("/chat", methods=["POST"])
def chat():
    phone = request.form.get("phone_number")
    msg = request.form.get("message")

    print(f"[TEST CHAT] 📲 {phone}: {msg}")

    response = MessagingResponse()
    response.message(f"Mock response to your message: {msg}")
    return Response(str(response), mimetype="application/xml")
