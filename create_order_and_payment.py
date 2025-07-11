# Версия 2.6 (2025-07-11)
# ✅ Вставка в pending_payments теперь с расширенным логированием

from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import APIRouter, Request
import os
import uuid
import httpx
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path="/opt/aianswerline/.env")

router = APIRouter()

SQUARE_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
SQUARE_LOCATION = os.getenv("SQUARE_LOCATION_ID")

print(f"🔍 SQUARE_LOCATION = {SQUARE_LOCATION}")
print(f"🔍 SQUARE_TOKEN    = {SQUARE_TOKEN[:8]}... (trimmed)")

@router.get("/create_order_payment")
async def create_order_payment(request: Request):
    try:
        phone = request.query_params["phone"]
        amount = int(request.query_params["amount"])
    except Exception as e:
        print(f"❌ Invalid parameters: {str(e)}", flush=True)
        return JSONResponse({"error": "Invalid parameters", "detail": str(e)}, status_code=400)

    order_idempotency_key = str(uuid.uuid4())
    payment_idempotency_key = f"{phone}-{amount}-{uuid.uuid4().hex[:6]}"

    headers = {
        "Authorization": f"Bearer {SQUARE_TOKEN}",
        "Content-Type": "application/json"
    }

    order_payload = {
        "idempotency_key": order_idempotency_key,
        "order": {
            "location_id": SQUARE_LOCATION,
            "line_items": [
                {
                    "name": "Token Purchase",
                    "quantity": "1",
                    "base_price_money": {
                        "amount": amount * 100,
                        "currency": "USD"
                    }
                }
            ],
            "reference_id": phone
        }
    }

    print(f"\n📤 [STEP 1] Creating order for ${amount}, phone: {phone}")
    print(f"📤 Payload:\n{order_payload}")

    async with httpx.AsyncClient() as client:
        order_resp = await client.post(
            "https://connect.squareup.com/v2/orders",
            headers=headers,
            json=order_payload
        )
        order_data = order_resp.json()
        print(f"📥 Order response [{order_resp.status_code}]:\n{order_data}")

        if order_resp.status_code != 200 or "order" not in order_data:
            print("❌ Order creation failed")
            return JSONResponse({"error": "Order creation failed", "raw": order_data}, status_code=500)

        payment_payload = {
            "idempotency_key": payment_idempotency_key,
            "order": {
                "location_id": SQUARE_LOCATION,
                "line_items": [
                    {
                        "name": "Token Purchase",
                        "quantity": "1",
                        "base_price_money": {
                            "amount": amount * 100,
                            "currency": "USD"
                        }
                    }
                ]
            },
            "checkout_options": {
                "redirect_url": "https://aianswerline.live",
                "custom_fields": [
                    {
                        "title": "Phone",
                        "value": phone
                    }
                ]
            }
        }

        print(f"\n💳 [STEP 2] Creating payment link for order...")
        print(f"💳 Payment payload:\n{payment_payload}")

        payment_resp = await client.post(
            "https://connect.squareup.com/v2/online-checkout/payment-links",
            headers=headers,
            json=payment_payload
        )
        payment_data = payment_resp.json()
        print(f"💳 Payment response [{payment_resp.status_code}]:\n{payment_data}")

        if payment_resp.status_code != 200 or "payment_link" not in payment_data:
            print("❌ No payment link returned")
            return JSONResponse({"error": "No payment link returned", "raw": payment_data}, status_code=500)

        url = payment_data["payment_link"]["url"]
        payment_link_id = payment_data["payment_link"]["id"]
        order_id = payment_data["payment_link"]["order_id"]
        print(f"🔗 Payment link:\n{url}\n🔑 PaymentLinkID: {payment_link_id}, OrderID: {order_id}")

        try:
            print(f"\n🗄 [STEP 3] Connecting to DB for INSERT pending_payment...")
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            conn.autocommit = True
            cur = conn.cursor()
            insert_query = """
                INSERT INTO pending_payments (
                    user_id, email, phone, order_id,
                    payment_link, payment_link_id, amount,
                    currency, status, fulfilled, created_at
                )
                SELECT id, email, phone, %s, %s, %s, %s,
                       'USD', 'pending', FALSE, NOW()
                FROM users WHERE phone = %s
            """
            print(f"📝 SQL:\n{insert_query}")
            print(f"📝 VALUES:\norder_id={order_id}, url={url}, payment_link_id={payment_link_id}, amount={amount}, phone={phone}")
            cur.execute(insert_query, (order_id, url, payment_link_id, amount, phone))
            print(f"✅ Insert successful for phone {phone}")
        except Exception as e:
            print(f"❌ Database insert error for phone {phone}:\n{str(e)}", flush=True)
            return JSONResponse({"error": "Database insert failed", "detail": str(e)}, status_code=500)

    print("🏁 DONE — redirecting to payment link...")
    return RedirectResponse(url=url, status_code=302)
