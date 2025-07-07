# payment_router.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import os, uuid, requests

router = APIRouter()

@router.get("/create_payment_link")
async def create_payment_link(amount: int, phone: str):
    location_id = os.getenv("SQUARE_LOCATION_ID")
    token = os.getenv("SQUARE_TOKEN")
    if not location_id or not token:
        raise HTTPException(status_code=500, detail="Square credentials not configured")

    body = {
        "idempotency_key": str(uuid.uuid4()),
        "quick_pay": {
            "name": "Token Purchase",
            "price_money": {
                "amount": amount,  # in cents
                "currency": "USD"
            },
            "location_id": location_id
        },
        "redirect_url": f"https://yourdomain.com/thankyou",  # позже заменим
        "reference_id": phone
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    r = requests.post("https://connect.squareup.com/v2/online-checkout/payment-links", json=body, headers=headers)

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Square error: {r.text}")

    data = r.json()
    return RedirectResponse(url=data["payment_link"]["url"])
