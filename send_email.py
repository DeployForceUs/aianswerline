# Версия 1.0 (2025-07-05)
# 📤 Отправка письма через Resend API

import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="/opt/aianswerline/.env")

def send_email(to_email: str, subject: str, html_body: str):
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM")

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

    response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
    return response.status_code, response.text
