# initial_test3.py — Тестирует /twilio-hook + проверка БД
import os
import time
import requests
import psycopg2
from dotenv import load_dotenv

print("🧪 Initial Test 3 — FastAPI /twilio-hook full logic")

# === Загрузка .env ===
env_path = "/opt/aianswerline/.env"
print(f"🔍 Loading .env from {env_path}...")
load_dotenv(dotenv_path=env_path)

# === Тестовые данные ===
phone = "+15558887777"
message = "InitialTest3 запуск логики"
print(f"📱 Phone: {phone}")
print(f"💬 Message: {message}")

# === Отправка запроса на /twilio-hook ===
url = "http://localhost:8000/twilio-hook"
data = {"From": phone, "Body": message}
print(f"🚀 POST {url} ...")
response = requests.post(url, data=data)

print(f"🌐 Status: {response.status_code}")
print(f"📨 Body:\n{response.text}")

# === Подключение к БД ===
print("🐘 Connecting to DB...")
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

# === Проверка создания пользователя ===
print("🔍 Checking users table...")
cur.execute("SELECT id, tokens_balance, created_at FROM users WHERE phone_number = %s", (phone,))
user = cur.fetchone()

if user:
    user_id, balance, created = user
    print(f"✅ User created: ID={user_id}, tokens={balance}, created_at={created}")
else:
    print("❌ User not found in DB.")

# === Проверка токен-лога ===
print("🔍 Checking tokens_log...")
cur.execute("SELECT change, source, description, created_at FROM tokens_log WHERE user_id = %s ORDER BY id DESC LIMIT 2", (user_id,))
rows = cur.fetchall()

if rows:
    for row in rows:
        change, source, desc, created = row
        print(f"  - {change:+} | {source} | {desc} | {created}")
else:
    print("❌ No token logs found.")

cur.close()
conn.close()
print("✅ initial_test3 complete.")
