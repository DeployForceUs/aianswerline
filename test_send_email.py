# test_send_email.py
from send_email import send_email

# Задай свою почту сюда для теста
test_email = "dimaretro@yahoo.com"

# Сообщение
subject = "🔍 TEST EMAIL — OTP System"
html = "<p>This is a <strong>test</strong> from your OTP system backend.</p>"

# Отправляем
status, response = send_email(test_email, subject, html)

print("=== TEST EMAIL RESULT ===")
print("Status:", status)
print("Response:", response)
