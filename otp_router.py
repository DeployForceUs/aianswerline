# Версия 2.4 (2025-07-06)
# 📩 OTP: PostgreSQL, лимит попыток, истечение срока, корректные ошибки

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import string
import psycopg2
import os

router = APIRouter()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
conn.autocommit = True
cur = conn.cursor()

from send_email import send_email

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

@router.post("/send_otp_email")
async def send_otp_email(email: str = Form(...)):
    code = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)

    cur.execute("""
        INSERT INTO email_otp (email, code, expires_at)
        VALUES (%s, %s, %s)
    """, (email, code, expires))

    html = f"<p>Your login code:</p><h2 style='font-family: monospace; letter-spacing: 4px'>{code}</h2><p>This code will expire in 10 minutes.</p>"
    status, text = send_email(email, "Your OTP Code", html)

    if status != 200:
        raise HTTPException(status_code=500, detail="Failed to send email")

    return JSONResponse(content={"message": "OTP sent"})

@router.post("/verify_otp")
async def verify_otp(email: str = Form(...), code: str = Form(...)):
    # Ищем самый последний неиспользованный код
    cur.execute("""
        SELECT id, code, expires_at, used, attempts
        FROM email_otp
        WHERE email = %s
        ORDER BY id DESC
        LIMIT 1
    """, (email,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="Code not found")

    otp_id, db_code, expires_at, used, attempts = row
    now = datetime.utcnow()

    # Логика проверки
    if used:
        raise HTTPException(status_code=400, detail="Code already used")

    if now > expires_at:
        raise HTTPException(status_code=400, detail="Code expired")

    if attempts >= 5:
        raise HTTPException(status_code=400, detail="Too many attempts")

    if code != db_code:
        cur.execute("UPDATE email_otp SET attempts = attempts + 1 WHERE id = %s", (otp_id,))
        raise HTTPException(status_code=400, detail="Invalid code")

    # Всё ок
    cur.execute("UPDATE email_otp SET used = TRUE WHERE id = %s", (otp_id,))
    return JSONResponse(content={"message": "Verified"})
