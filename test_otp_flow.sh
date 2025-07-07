#!/bin/bash

echo "📧 Введите email для теста:"
read EMAIL

echo "📡 Отправка OTP на $EMAIL..."
curl -s -X POST http://localhost:8000/send_otp_email \
  -F "email=$EMAIL" | tee /tmp/otp_send_response.json

echo -e "\n📨 Проверь почту и введи код:"
read CODE

echo "✅ Проверка кода..."
curl -s -X POST http://localhost:8000/verify_otp \
  -F "email=$EMAIL" \
  -F "code=$CODE" | tee /tmp/otp_verify_response.json

echo -e "\n🔍 Проверка, появился ли юзер в таблице users..."
psql -U twilio -d twiliogateway -c "SELECT * FROM users WHERE email = '$EMAIL';"
