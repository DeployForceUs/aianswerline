# initial_test.py
# Версия 1.0 (2025-07-04)
# ✅ Проверка .env
# ✅ Проверка подключения к PostgreSQL
# ✅ Проверка OpenAI API
# ✅ Проверка Twilio API

import os
import traceback
from dotenv import load_dotenv
import psycopg2
from openai import OpenAI
from twilio.rest import Client

print("🧪 Starting Initial Test Script...\n")

# === .env ===
print("📄 Loading .env from /opt/aianswerline/.env...")
if load_dotenv(dotenv_path="/opt/aianswerline/.env"):
    print("✅ .env loaded\n")
else:
    print("❌ Failed to load .env\n")

# === Проверка env переменных ===
print("🔍 Environment Variables:")
env_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS", "OPENAI_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE"]
for var in env_vars:
    status = "✅" if os.getenv(var) else "❌"
    print(f"  {var}: {status}")
print()

# === PostgreSQL ===
print("🐘 Testing PostgreSQL connection...")
try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    rows = cur.fetchall()
    print("✅ PostgreSQL OK. Tables found:")
    for schema, name in rows:
        print(f"   - {schema}.{name}")
except Exception:
    print("❌ PostgreSQL ERROR:")
    traceback.print_exc()
print()

# === OpenAI ===
print("🧠 Testing OpenAI API key...")
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    models = client.models.list()
    print(f"✅ OpenAI OK. Found {len(models.data)} models.")
except Exception:
    print("❌ OpenAI ERROR:")
    traceback.print_exc()
print()

# === Twilio ===
print("📞 Testing Twilio credentials...")
try:
    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    incoming_numbers = twilio_client.incoming_phone_numbers.list(limit=1)
    if incoming_numbers:
        print(f"✅ Twilio OK. First phone: {incoming_numbers[0].phone_number}")
    else:
        print("⚠️ Twilio connected, but no numbers found.")
except Exception:
    print("❌ Twilio ERROR:")
    traceback.print_exc()
print()

print("✅ Test script complete.")
