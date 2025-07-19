# Версия 1.4 (2025-07-12)
# ✅ Формат B: все колонки, значения без подрезки
# ✅ Только pending_payments
# ✅ Поддержка Aiogram 3.x (через F)
# ✅ Безопасность: только для admin ID

import asyncio
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BOT_ADMIN = 394521639
BOT_TOKEN = "8015957343:AAGPc_6tNODmJDzee11oF4lkMgbF2r30koc"

DB_CONFIG = {
    "user": "twilio",
    "password": "SuperSecret",
    "database": "twiliogateway",
    "host": "172.18.0.2",
    "port": "5432"
}

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📄 pending_payments")]],
    resize_keyboard=True
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def is_admin(user_id: int) -> bool:
    return user_id == BOT_ADMIN

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Access denied.")
    await message.answer("📊 Choose a table to view:", reply_markup=main_keyboard)

@dp.message(F.text == "📄 pending_payments")
async def show_pending_payments(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Access denied.")
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        rows = await conn.fetch("SELECT id, email, phone, order_id, payment_link, amount, status, created_at FROM pending_payments ORDER BY id DESC LIMIT 5")
        await conn.close()

        if not rows:
            return await message.answer("🕳 Table is empty.")

        # Формируем таблицу
        response = "```\n"
        response += f"{'ID':<3} | {'Email':<27} | {'Phone':<12} | {'Order ID':<20} | {'Link':<36} | {'Amt':<5} | {'Status':<8} | Created At\n"
        response += "-" * 135 + "\n"
        for r in rows:
            response += f"{r['id']:<3} | {r['email']:<27} | {r['phone']:<12} | {r['order_id']:<20} | {r['payment_link']:<36} | {r['amount']:<5} | {r['status']:<8} | {str(r['created_at'])[:19]}\n"
        response += "```"

        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"⚠️ Error: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
