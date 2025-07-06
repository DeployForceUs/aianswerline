#!/bin/bash

source /opt/aianswerline/.env

EMAIL="dimabmw@me.com"

echo "📡 1. Отправляем OTP на $EMAIL..."
RESPONSE=$(curl -s -X POST http://localhost:8000/send_otp_email -F "email=$EMAIL")
echo "🔄 Ответ от сервера: $RESPONSE"

echo "⏳ 2. Ждём 10 секунд, чтобы код записался в PostgreSQL..."
sleep 10

echo "🔍 3. Достаём код из PostgreSQL..."
CODE=$(PGPASSWORD="$PG_PASS" psql -h "$PG_HOST" -U "$PG_USER" -d "$PG_DB" -t -A -c "SELECT code FROM email_otp WHERE email = '$EMAIL' ORDER BY created_at DESC LIMIT 1;")

echo "📦 Код из базы: $CODE"

if [ -z "$CODE" ]; then
    echo "❌ Код не найден. Прерываем."
    exit 1
fi

echo "🚀 4. Отправляем код на проверку..."
VERIFY=$(curl -s -X POST http://localhost:8000/verify_otp -F "email=$EMAIL" -F "code=$CODE")

echo "🎯 Ответ: $VERIFY"
