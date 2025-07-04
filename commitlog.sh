#!/bin/bash
msg="$1"
if [ -z "$msg" ]; then
  echo "❌ Укажи сообщение для лога. Пример: ./commitlog.sh 'Обновили Stripe'"
  exit 1
fi

python3 add_log.py "$msg"
git add .
git commit -m "$msg"
git push
