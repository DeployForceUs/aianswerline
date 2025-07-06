# Версия 2.0 (2025-07-06)
# 📩 OTP: Отправка и проверка кода через Redis

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import string
import redis  # 🧠 Новый импорт

from send_email import send_email

router = APIRouter()

# 🔌 Подключение к Redis
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

@router.post("/send_otp_email")
async def send_otp_email(email: str = Form(...)):
    code = generate_otp()
    key = f"otp:{email}"
    payload = {
        "code": code,
        "expires": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }
    r.setex(key, timedelta(minutes=10), str(payload))

    html = f"<p>Your login code:</p><h2 style='font-family: monospace; letter-spacing: 4px'>{code}</h2><p>This code will expire in 10 minutes.</p>"
    status, text = send_email(email, "Your OTP Code", html)

    if status != 200:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return JSONResponse(content={"message": "OTP sent"})

@router.post("/verify_otp")
async def verify_otp(email: str = Form(...), code: str = Form(...)):
    key = f"otp:{email}"
    raw = r.get(key)

    if not raw:
        raise HTTPException(status_code=400, detail="Code not found or expired")

    try:
        record = eval(raw)
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupted OTP record")

    if record["code"] != code:
        raise HTTPException(status_code=400, detail="Invalid code")

    if datetime.utcnow() > datetime.fromisoformat(record["expires"]):
        raise HTTPException(status_code=400, detail="Code expired")

    r.delete(key)
    return JSONResponse(content={"message": "Verified"})
