# Версия 1.4 (2025-07-07)
# Проверка .env + подключение к Docker PostgreSQL + вставка в email_otp

import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/opt/aianswerline/.env")

print("📦 Проверка переменных окружения:")
for var in ["DB_NAME", "DB_USER", "DB_PASS", "DB_HOST", "DB_PORT"]:
    print(f"  🔹 {var} = {os.getenv(var)}")

if not all([os.getenv("DB_NAME"), os.getenv("DB_USER"), os.getenv("DB_PASS"), os.getenv("DB_HOST"), os.getenv("DB_PORT")]):
    print("❌ Ошибка: не все переменные окружения заданы.")
    exit(1)

print("\n🔌 Попытка подключения к базе данных...")
try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    print("✅ Подключение успешно.")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    exit(1)

cur = conn.cursor()
email = "dimatest@failcase.com"
code = "999999"
expires = datetime.utcnow()

print("\n📥 Вставка в таблицу email_otp:")
print(f"  🔸 Email:   {email}")
print(f"  🔸 Code:    {code}")
print(f"  🔸 Expires: {expires}")

try:
    cur.execute(
        "INSERT INTO email_otp (email, code, expires_at) VALUES (%s, %s, %s)",
        (email, code, expires)
    )
    conn.commit()
    print("✅ Успешно вставлено!")
except Exception as e:
    print(f"❌ Ошибка при вставке: {e}")
finally:
    cur.close()
    conn.close()
