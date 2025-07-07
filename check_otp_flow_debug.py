# check_otp_flow_debug.py
# Версия 1.0 (2025-07-07)
# 🔎 Подробная диагностика отправки кода
# Показывает входящий email, лог генерации кода и SMTP-ответ

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
import smtplib, random, string
from email.mime.text import MIMEText
from datetime import datetime
import psycopg2

app = FastAPI()

@app.post("/debug_send_otp")
async def debug_send_otp(email: str = Form(...)):
    print(f"\n=== [STEP 1] Входящий email: {email} ===")

    code = ''.join(random.choices(string.digits, k=6))
    expires = datetime.utcnow().isoformat()
    print(f"[STEP 2] Сгенерирован код: {code}, истекает: {expires}")

    try:
        # DB insert
        conn = psycopg2.connect(host="localhost", dbname="twiliogateway", user="twilio", password="twilio")
        cur = conn.cursor()
        cur.execute("INSERT INTO email_otp (email, code, used, expires_at) VALUES (%s, %s, %s, %s)", 
                    (email, code, False, datetime.utcnow()))
        conn.commit()
        cur.close()
        conn.close()
        print("[STEP 3] Код вставлен в базу.")
    except Exception as e:
        print("[DB ERROR]", e)
        return JSONResponse(status_code=500, content={"error": "DB insert failed"})

    try:
        msg = MIMEText(f"Your OTP code is {code}")
        msg["Subject"] = "OTP Code"
        msg["From"] = "noreply@yourdomain.com"
        msg["To"] = email

        with smtplib.SMTP("localhost") as server:
            server.send_message(msg)
        print("[STEP 4] SMTP успешно отправлен.")
        return {"message": "OTP sent"}
    except Exception as e:
        print("[SMTP ERROR]", e)
        return JSONResponse(status_code=500, content={"error": "SMTP failed"})
