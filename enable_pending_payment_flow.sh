#!/bin/bash

echo "[1] 🎯 Переходим в директорию проекта..."
cd /opt/aianswerline || exit 1

echo "[2] 🛠 Обновляем create_order_and_payment.py..."
touch create_order_and_payment.py  # заглушка на случай отсутствия
# Здесь могла бы быть замена или вставка нового кода, если нужно

echo "[3] ⏭ Пропускаем обновление square_webhook.py (файл отсутствует)..."

echo "[4] ✅ Проверим, что маршрут /after_payment есть в main.py..."
if grep -q "after_payment" main.py; then
  echo "🔍 Маршрут уже есть."
else
  echo "⚠️ Маршрут /after_payment не найден. Добавь вручную, если нужно."
fi

echo "[5] 🚀 Перезапускаем fastapi-gateway.service..."
systemctl restart fastapi-gateway.service

if systemctl is-active --quiet fastapi-gateway.service; then
  echo "[✔️] Готово! Сервис успешно перезапущен. Дышим ровно."
else
  echo "[❌] Ошибка при перезапуске! Глянь:"
  systemctl status fastapi-gateway.service
fi
