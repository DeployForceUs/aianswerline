# Версия 1.0 (2025-07-06)
# 📞 Test Bind Phone — проверка запроса с логированием

import requests
import datetime

# Данные
email = "dimaretro@yahoo.com"
phone = "+12345678999"
url = "http://localhost:8000/bind_phone"

# Время для лога
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"bind_test_{timestamp}.log"

# Формируем payload
data = {
    "email": email,
    "phone": phone
}

# Отправляем запрос
try:
    response = requests.post(url, data=data)
    status = f"Status Code: {response.status_code}"
    headers = f"Headers:\n{response.headers}"
    body = f"Body:\n{response.text}"
    output = f"==== TEST BIND PHONE ====\n{status}\n\n{headers}\n\n{body}\n"

    print(output)

    with open(log_file, "w") as f:
        f.write(output)

    print(f"📁 Log saved: {log_file}")

except Exception as e:
    print(f"❌ ERROR: {e}")
