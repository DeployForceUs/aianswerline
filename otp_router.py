# Версия 4.0 (2025-07-11)
# ✅ Логика регистрации перенесена в bind_phone
# ✅ verify_otp только помечает OTP как использованный
# ✅ bind_phone делает всё: логин, привязка, создание
# ✅ Избегаем дублей: ни email, ни phone больше не создаются отдельно

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import psycopg2
import os
from datetime import datetime, timedelta
from send_email import send_email  # 📤 импорт функции отправки письма

router = APIRouter()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS")
}

def get_db_conn():
    return psycopg2.connect(**DB_CONFIG)

@router.post("/send_otp_email")
async def send_otp_email(email: str = Form(...)):
    try:
        email = email.lower()
        conn = get_db_conn()
        cur = conn.cursor()

        code = str(int(datetime.utcnow().timestamp()))[-6:]  # псевдо-OTP
        now = datetime.utcnow()
        expires = now + timedelta(minutes=5)

        cur.execute("""
            INSERT INTO email_otp (email, code, expires_at, used, attempts, sent_at)
            VALUES (%s, %s, %s, FALSE, 0, %s)
        """, (email, code, expires, now))
        conn.commit()

        subject = "Your AI AnswerLine OTP Code"
        html_body = f"<h3>Your code:</h3><p><b>{code}</b></p><p>Expires in 5 minutes.</p>"

        status_code, response = send_email(email, subject, html_body)
        if status_code not in (200, 202):
            return JSONResponse(status_code=500, content={"detail": f"Email send failed: {response}"})

        return JSONResponse(content={"message": "OTP sent"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
    finally:
        if conn:
            conn.close()

@router.post("/verify_otp")
async def verify_otp(email: str = Form(...), code: str = Form(...)):
    try:
        email = email.lower()
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, code, expires_at, used 
            FROM email_otp 
            WHERE LOWER(email) = LOWER(%s)
            ORDER BY id DESC LIMIT 1
        """, (email,))
        row = cur.fetchone()
        if not row:
            return JSONResponse(status_code=400, content={"detail": "Email not found."})

        otp_id, db_code, expires, used = row

        if db_code != code:
            cur.execute("UPDATE email_otp SET attempts = attempts + 1 WHERE id = %s", (otp_id,))
            conn.commit()
            return JSONResponse(status_code=400, content={"detail": "Invalid code."})

        if used:
            return JSONResponse(status_code=400, content={"detail": "Code already used."})
        if datetime.utcnow() > expires:
            return JSONResponse(status_code=400, content={"detail": "Code expired."})

        cur.execute("UPDATE email_otp SET used = TRUE WHERE id = %s", (otp_id,))
        conn.commit()

        return JSONResponse(content={"message": "OTP verified", "otp_verified": True})

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
    finally:
        if conn:
            conn.close()

@router.post("/bind_phone")
async def bind_phone(email: str = Form(...), phone: str = Form(...)):
    try:
        email = email.lower()
        conn = get_db_conn()
        cur = conn.cursor()

        # Сначала проверим, есть ли уже такой пользователь по email
        cur.execute("SELECT id, phone, tokens_balance FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        user = cur.fetchone()
        if user:
            _, phone_db, tokens = user
            return JSONResponse(content={
                "message": "Logged in",
                "linked": True,
                "phone": phone_db,
                "email": email,
                "tokens": tokens
            })

        # Ищем по номеру запись без email
        cur.execute("""
            SELECT id, tokens_balance FROM users 
            WHERE phone = %s AND email IS NULL
            ORDER BY id DESC LIMIT 1
        """, (phone,))
        phone_user = cur.fetchone()
        if phone_user:
            user_id, tokens = phone_user
            cur.execute("UPDATE users SET email = %s WHERE id = %s", (email, user_id))
            conn.commit()
            return JSONResponse(content={
                "message": "Email linked to existing phone",
                "linked": True,
                "phone": phone,
                "email": email,
                "tokens": tokens
            })

        # Новый пользователь
        now = datetime.utcnow()
        cur.execute("""
            INSERT INTO users (email, phone, tokens_balance, created_at)
            VALUES (%s, %s, 0, %s)
        """, (email, phone, now))
        conn.commit()

        return JSONResponse(content={
            "message": "New user created",
            "linked": True,
            "phone": phone,
            "email": email,
            "tokens": 0
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
    finally:
        if conn:
            conn.close()
