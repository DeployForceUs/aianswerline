# Версия 1.0 (2025-07-05)
# 📩 OTP: Отправка и проверка кода через email

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import string

from send_email import send_email

router = APIRouter()

# 🔒 Простая in-memory база (в проде — Redis или БД)
otp_store = {}  # email -> {"code": "123456", "expires": datetime}

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

@router.post("/send_otp_email")
async def send_otp_email(email: str = Form(...)):
    code = generate_otp()
    otp_store[email] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=10)
    }

    html = f"<h1>🔐 Your code is: {code}</h1><p>Use it to login.</p>"
    status, text = send_email(email, "Your OTP Code", html)

    if status != 200:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return JSONResponse(content={"message": "OTP sent"})

@router.post("/verify_otp")
async def verify_otp(email: str = Form(...), code: str = Form(...)):
    record = otp_store.get(email)
    if not record or record["code"] != code:
        raise HTTPException(status_code=400, detail="Invalid code")

    if datetime.utcnow() > record["expires"]:
        raise HTTPException(status_code=400, detail="Code expired")

    return JSONResponse(content={"message": "Verified"})
