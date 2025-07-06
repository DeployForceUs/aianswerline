#!/bin/bash

EMAIL="dimabmw@me.com"

echo "📡 1. Отправляем OTP на $EMAIL..."
RESPONSE=$(curl -s -X POST http://localhost:8000/send_otp_email -F "email=$EMAIL")
echo "🔄 Ответ от сервера: $RESPONSE"

echo "⏳ 2. Ждём 10 секунд, чтобы Redis успел сохранить..."
sleep 10

KEY="otp:$EMAIL"
echo "🔍 3. Достаём код из Redis..."
RAW=$(redis-cli GET "$KEY")
echo "🔑 Ключ в Redis: $KEY"
echo "📦 Содержимое ключа (оригинал): $RAW"

if [[ "$RAW" == "" ]]; then
    echo "❌ Код не найден. Прерываем."
    exit 1
fi

CODE=$(echo "$RAW" | sed -E "s/.*'code': '([0-9]+)'.*/\1/")

if [[ "$CODE" == "" ]]; then
    echo "❌ Код не найден в JSON. Прерываем."
    exit 1
fi

echo "✅ Код: $CODE"

echo "🚀 4. Отправляем код на проверку..."
VERIFY_RESPONSE=$(curl -s -X POST http://localhost:8000/verify_otp -F "email=$EMAIL" -F "code=$CODE")

if echo "$VERIFY_RESPONSE" | grep -q "Verified"; then
    echo "🎯 Всё успешно: $VERIFY_RESPONSE"
else
    echo "❌ Ошибка подтверждения: $VERIFY_RESPONSE"
    exit 1
fi
