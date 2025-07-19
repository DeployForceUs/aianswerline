# Версия 4.1 (2025-07-16)
# 🔕 Отключена вся вставка/создание пользователей после верификации OTP
# 🔒 Только проверяем код и завершаем, остальное отключено по бизнес-решению
# ✅ Строчка "Отметим, что код использован" оставлена, всё остальное закомментировано
# ❌ bind_phone полностью закомментирован, маршрут отключён
# ☑️ Количество строк строго сохранено

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
            ORDER BY id DESC 
            LIMIT 1
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

        # Отметим, что код использован
        cur.execute("UPDATE email_otp SET used = TRUE WHERE id = %s", (otp_id,))
        conn.commit()

        # === Всё ниже отключено ===
        """
        # Проверим: есть ли юзер с этим email
        cur.execute("""
            SELECT id, phone, tokens_balance 
            FROM users 
            WHERE LOWER(email) = LOWER(%s)
        """, (email,))
        user = cur.fetchone()

        if user:
            _, phone, tokens = user
            linked = phone is not None

        else:
            # Ищем последнего юзера без email, но с номером — через SMS
            cur.execute("""
                SELECT id, phone, tokens_balance 
                FROM users 
                WHERE email IS NULL AND phone IS NOT NULL
                ORDER BY id DESC LIMIT 1
            """)
            phone_user = cur.fetchone()

            if phone_user:
                user_id, phone, tokens = phone_user
                cur.execute("UPDATE users SET email = %s WHERE id = %s", (email, user_id))
                conn.commit()
                linked = True
            else:
                # Новый пользователь — ни email, ни phone нет
                cur.execute("""
                    INSERT INTO users (email, tokens_balance, created_at)
                    VALUES (%s, %s, %s)
                """, (email, 0, datetime.utcnow()))
                conn.commit()
                linked = False
                phone = None
                tokens = 0

        return JSONResponse(content={
            "message": "Verified",
            "linked": linked,
            "phone": phone,
            "email": email,
            "tokens": tokens,
            "used": True
        })
        """

        return JSONResponse(content={
            "message": "Verified",
            "email": email,
            "used": True
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
    finally:
        if conn:
            conn.close()

"""
@router.post("/bind_phone")
async def bind_phone(email: str = Form(...), phone: str = Form(...)):
    try:
        email = email.lower()
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("UPDATE users SET phone = %s WHERE LOWER(email) = LOWER(%s)", (phone, email))
        conn.commit()

        cur.execute("SELECT tokens_balance FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        row = cur.fetchone()
        tokens = row[0] if row else 0

        return JSONResponse(content={
            "message": "Verified",
            "linked": True,
            "phone": phone,
            "email": email,
            "tokens": tokens
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

    finally:
        if conn:
            conn.close()
"""

