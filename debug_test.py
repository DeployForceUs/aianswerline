# debug_test.py — версия 1.0
import os
from dotenv import load_dotenv

print("🔍 Загружаем .env...")
load_dotenv("/opt/aianswerline/.env")

env = os.getenv("SQUARE_ENVIRONMENT")
token = os.getenv("SQUARE_ACCESS_TOKEN")
loc_id = os.getenv("SQUARE_LOCATION_ID")

print(f"SQUARE_ENVIRONMENT = {env}")
print(f"SQUARE_ACCESS_TOKEN = {token[:6]}...{token[-4:]}")
print(f"SQUARE_LOCATION_ID = {loc_id}")

try:
    from squareup.client import Client
    print("✅ Импорт squareup.client прошёл успешно")
except Exception as e:
    print("💥 Ошибка при импорте squareup.client:", e)
    exit(1)

try:
    client = Client(access_token=token, environment=env)
    print("✅ Клиент Square инициализирован")
except Exception as e:
    print("💥 Ошибка при создании клиента:", e)
    exit(2)

try:
    resp = client.payments_api.create_payment(body={
        "source_id": "cnon:card-nonce-ok",
        "idempotency_key": "test-debug-001",
        "amount_money": {
            "amount": 199,
            "currency": "USD"
        },
        "location_id": loc_id
    })
    if resp.is_success():
        print("✅ Платёж прошёл:", resp.body)
    else:
        print("❌ Платёж не прошёл:", resp.errors)

except Exception as e:
    print("💥 Ошибка при попытке оплаты:", e)
    exit(3)
