from send_email import send_email

status, text = send_email(
    to_email="dimaretro@yahoo.com",
    subject="Test OTP Code",
    html_body="<h1>🔐 Your code is: 123456</h1><p>Use it to login.</p>"
)

print("Status:", status)
print("Response:", text)
