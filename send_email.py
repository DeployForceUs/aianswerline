# Версия 1.1 (2025-07-07)
# 📤 Resend + Verbose Logging

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path="/opt/aianswerline/.env")

def send_email(to_email: str, subject: str, html_body: str):
    log_path = "/opt/aianswerline/tmp/resend_debug.log"

    def log(message):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    log("📨 send_email called")
    log(f"To: {to_email}, Subject: {subject}")

    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM")

    if not api_key or not from_email:
        log("❌ Missing RESEND_API_KEY or RESEND_FROM in .env")
        return 500, "Missing email config"

    payload = {
        "from": from_email,
        "to": to_email,
        "subject": subject,
        "html": html_body
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        log("🌐 Sending POST to Resend API")
        response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        log(f"✅ Response {response.status_code}: {response.text}")
        return response.status_code, response.text
    except Exception as e:
        log(f"❌ Exception during send: {str(e)}")
        return 500, str(e)
