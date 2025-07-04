# Версия 1.0 (2025-07-03)
# ✅ Приём номера и суммы оплаты
# ✅ Начисление токенов в users
# ✅ Логирование в tokens_log

import os
import psycopg2
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path="/var/www/aianswerline/api/.env")

conn = psycopg2.connect(
    dbname="twilio",
    user="twilio",
    password="SuperSecret",
    host="172.18.0.2",
    port="5432"
)
conn.autocommit = True
cur = conn.cursor()

app = Flask(__name__)

@app.route("/token-up", methods=["POST"])
def token_up():
    phone = request.form.get("phone_number")
    amount_paid = request.form.get("amount_paid")

    if not phone or not amount_paid:
        return jsonify({"error": "Missing phone_number or amount_paid"}), 400

    try:
        amount_paid = float(amount_paid)
        tokens_to_add = int(amount_paid / 0.05)
    except:
        return jsonify({"error": "Invalid amount"}), 400

    # Проверка пользователя
    cur.execute("SELECT id FROM users WHERE phone_number = %s", (phone,))
    user = cur.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user[0]

    # Обновление баланса
    cur.execute("UPDATE users SET tokens_balance = tokens_balance + %s WHERE id = %s", (tokens_to_add, user_id))

    # Логирование
    cur.execute("""
        INSERT INTO tokens_log (user_id, change, source, description, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, tokens_to_add, 'payment', f"Payment of ${amount_paid}", datetime.utcnow()))

    return jsonify({"status": "ok", "tokens_added": tokens_to_add})
