# initial_test2.py
# Версия 2.0 (2025-07-04)
# - Проверка /chat
# - Проверка создания пользователя
# - Проверка записи в tokens_log

import requests
import os
import psycopg2
from dotenv import load_dotenv

print("🧪 Starting Initial Test 2 — FastAPI /chat endpoint + DB check...")
load_dotenv("/opt/aianswerline/.env")
print("✅ .env loaded from /opt/aianswerline/.env")

# Vars
url = "http://localhost:8000/chat"
test_phone = "+15559990001"
test_message = "Проверка InitialTest2"
DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
}

print(f"📍 Endpoint: {url}")
print(f"📱 Phone: {test_phone}")
print(f"💬 Message: {test_message}")
print("🚀 Sending request...")

# Send request
r = requests.post(url, data={"phone_number": test_phone, "message": test_message})

print(f"\n🌐 Response status: {r.status_code}")
print(f"📨 Response text: {r.text.strip()}")

# Check DB
print("\n🔍 Checking DB for new user and token log...")
conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

cur.execute("SELECT id FROM users WHERE phone_number = %s ORDER BY id DESC LIMIT 1", (test_phone,))
user = cur.fetchone()

if user:
    print(f"✅ User created: ID {user[0]}")
    cur.execute("SELECT change, description, created_at FROM tokens_log WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user[0],))
    log = cur.fetchone()
    if log:
        print(f"✅ Token log: change={log[0]}, desc='{log[1]}', time={log[2]}")
    else:
        print("❌ No token log found.")
else:
    print("❌ User not created.")

cur.close()
conn.close()

print("\n✅ Initial Test 2 complete.")
