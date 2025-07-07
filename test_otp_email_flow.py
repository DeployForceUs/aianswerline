# Версия 1.1 (2025-07-07)
# ✅ Тестовый флоу отправки OTP с рабочим email
# ✅ Подробный лог сохраняется в tmp/

import requests
from datetime import datetime

log_path = f"/opt/aianswerline/tmp/email_flow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
test_email = "verify@aianswerline.live"  # ✅ рабочий email

def log(msg):
    print(msg)
    with open(log_path, "a") as f:
        f.write(msg + "\n")

log(f"🔍 STEP 1: Sending POST /send_otp_email")
form_data = {
    "email": test_email
}

resp = requests.post("http://localhost:8000/send_otp_email", data=form_data)
log("🧾 Status: " + str(resp.status_code))
try:
    log("📦 Body: " + str(resp.json()))
except Exception:
    log("📦 Body: " + resp.text)

log(f"✅ Finished. Log saved to: {log_path}")
