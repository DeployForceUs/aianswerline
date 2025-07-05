#!/usr/bin/env python3
# Версия 1.0.0 (2025-07-04)
# Скрипт для автоматического добавления строк в CHANGELOG.md

from datetime import datetime
import sys

if len(sys.argv) < 2:
    print("❗️ Использование: python3 add_log.py \"описание шага\"")
    sys.exit(1)

entry = sys.argv[1]
date = datetime.now().strftime("## %Y-%m-%d")

with open("CHANGELOG.md", "r+") as f:
    content = f.read()
    if date not in content:
        f.seek(0)
        f.write(f"# CHANGELOG\n\n{date}\n- {entry}\n\n" + content.replace("# CHANGELOG\n", "").strip())
    else:
        # вставим строку после нужной даты
        parts = content.split(date)
        new_content = parts[0] + date + "\n- " + entry + parts[1]
        f.seek(0)
        f.write(new_content)
        f.truncate()

print(f"✅ Добавлено в CHANGELOG.md: {entry}")
