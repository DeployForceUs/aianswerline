# Версия 1.1 (2025-07-15)
# ✅ добавлено подключение к PostgreSQL через asyncpg
# ✅ команда /list делает SQL-запрос и отправляет результат
# ✅ обработка ошибок с выводом в Telegram
# ✅ поддержка .env-переменных из DB_*

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import asyncpg

# Подгружаем .env
load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID"))

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Логирование
logging.basicConfig(level=logging.INFO)

# Бот
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("list"))
async def handle_list(message: Message):
    try:
        await message.answer("✅ Принято: /list\n⏳ Получаю данные...")

        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )

        rows = await conn.fetch("SELECT id, phone, created_at FROM users ORDER BY id DESC LIMIT 10;")
        await conn.close()

        if not rows:
            await message.answer("❗️Нет данных в таблице `users`.")
            return

        reply = "<b>Последние пользователи:</b>\n\n"
        for row in rows:
            reply += f"🆔 <code>{row['id']}</code>\n📱 <code>{row['phone']}</code>\n🕒 <code>{row['created_at']}</code>\n\n"

        await message.answer(reply)

    except Exception as e:
        await message.answer(f"❌ Ошибка:\n<code>{str(e)}</code>")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
