# Версия 3.0 (2025-07-06)
# 📩 OTP: Отправка и проверка кода через PostgreSQL

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import string
import os
import psycopg2

from send_email import send_email

router = APIRouter()

# Подключение к PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
conn.autocommit = True
cur = conn.cursor()

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

@router.post("/send_otp_email")
async def send_otp_email(email: str = Form(...)):
    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Запись кода в таблицу
    cur.execute("""
        INSERT INTO email_otp (email, code, expires_at)
        VALUES (%s, %s, %s)
    """, (email, code, expires_at))

    # Отправка письма
    html = f"<p>Your login code:</p><h2 style='font-family: monospace; letter-spacing: 4px'>{code}</h2><p>This code will expire in 10 minutes.</p>"
    status, text = send_email(email, "Your OTP Code", html)

    if status != 200:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return JSONResponse(content={"message": "OTP sent"})

@router.post("/verify_otp")
async def verify_otp(email: str = Form(...), code: str = Form(...)):
    cur.execute("""
        SELECT id, expires_at, used FROM email_otp
        WHERE email = %s AND code = %s
        ORDER BY id DESC
        LIMIT 1
    """, (email, code))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="Invalid code")

    otp_id, expires_at, used = row

    if used:
        raise HTTPException(status_code=400, detail="Code already used")

    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Code expired")

    # Обновляем как использованный
    cur.execute("UPDATE email_otp SET used = TRUE WHERE id = %s", (otp_id,))
    return JSONResponse(content={"message": "Verified"})
