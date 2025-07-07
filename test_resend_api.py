import requests

api_key = "re_2pYYZJUD_CrekVqrutjmEz9QXE3x2z3T2"
from_email = "verify@aianswerline.live"
to_email = "your@email.com"  # ← замени на свой
subject = "Test Resend"
html_body = "<h1>Resend API check</h1><p>This is a test email.</p>"

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

print(f"Status: {response.status_code}")
print("Response:")
print(response.text)
