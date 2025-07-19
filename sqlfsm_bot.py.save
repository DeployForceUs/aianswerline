# Версия 1.7.0 (2025-07-15)
# ✅ Чтение конфигурации из .env
# ✅ Сохранение временных файлов в /opt/tmpfiles
# ✅ Вывод в форматах JSON, TEXT, MARKDOWN, HTML
# ✅ Выбор таблицы, лимита (первые/последние 10)
# ✅ Защита от чужих юзеров

import asyncio
import asyncpg
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ADMIN = int(os.getenv("BOT_ADMIN"))

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

TABLES = ["pending_payments", "tokens_log", "users", "transactions"]
LIMITS = [("first", "⏫ Первые 10"), ("last", "⏬ Последние 10")]
FORMATS = [("json", "📦 JSON"), ("text", "📋 Текст"), ("markdown", "📄 Markdown"), ("html", "🪟 HTML")]

TMP_DIR = "/opt/tmpfiles"
os.makedirs(TMP_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class ViewState(StatesGroup):
    table = State()
    limit = State()
    fmt = State()

def get_table_kb():
    kb = InlineKeyboardBuilder()
    for t in TABLES:
        kb.row(InlineKeyboardButton(text=f"📄 {t}", callback_data=f"table:{t}"))
    return kb.as_markup()

def get_limit_kb():
    kb = InlineKeyboardBuilder()
    for key, label in LIMITS:
        kb.row(InlineKeyboardButton(text=label, callback_data=f"limit:{key}"))
    return kb.as_markup()

def get_format_kb():
    kb = InlineKeyboardBuilder()
    for key, label in FORMATS:
        kb.row(InlineKeyboardButton(text=label, callback_data=f"fmt:{key}"))
    return kb.as_markup()

def format_as_table(rows, as_markdown=False):
    if not rows:
        return ""
    headers = list(rows[0].keys())
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row.values()):
            col_widths[i] = max(col_widths[i], len(str(val)))
    sep = " | " if as_markdown else "  "
    lines = []

    header_line = sep.join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)

    if as_markdown:
        lines.append(sep.join('-' * col_widths[i] for i in range(len(headers))))

    for row in rows:
        line = sep.join(str(val).ljust(col_widths[i]) for i, val in enumerate(row.values()))
        lines.append(line)

    return "\n".join(lines)

def format_as_html(rows):
    if not rows:
        return ""
    headers = list(rows[0].keys())
    html = "<table border='1'>\n<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>\n"
    for row in rows:
        html += "<tr>" + "".join(f"<td>{val}</td>" for val in row.values()) + "</tr>\n"
    html += "</table>"
    return html

@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    if message.from_user.id != BOT_ADMIN:
        return await message.answer("⛔ Access denied.")
    await state.clear()
    await state.set_state(ViewState.table)
    await message.answer("Выбери таблицу:", reply_markup=get_table_kb())

@dp.callback_query(F.data.startswith("table:"))
async def select_table(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(table=callback.data.split(":")[1])
    await state.set_state(ViewState.limit)
    await callback.message.edit_text("Сколько строк вывести?", reply_markup=get_limit_kb())

@dp.callback_query(F.data.startswith("limit:"))
async def select_limit(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(limit=callback.data.split(":")[1])
    await state.set_state(ViewState.fmt)
    await callback.message.edit_text("Выбери формат вывода:", reply_markup=get_format_kb())

@dp.callback_query(F.data.startswith("fmt:"))
async def select_format(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(fmt=callback.data.split(":")[1])
    data = await state.get_data()
    await state.clear()

    table = data["table"]
    limit_type = data["limit"]
    fmt = data["fmt"]

    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        order = "ASC" if limit_type == "first" else "DESC"
        rows = await conn.fetch(f"SELECT * FROM {table} ORDER BY id {order} LIMIT 10")
        await conn.close()

        if not rows:
            await callback.message.edit_text("🕳 Table is empty.")
            await callback.message.answer("Выбери таблицу:", reply_markup=get_table_kb())
            return

        filename = f"{TMP_DIR}/output_{table}_{limit_type}.{fmt}"

        if fmt == "json":
            response = json.dumps([dict(r) for r in rows], indent=2, default=str)
            if len(response) < 4000:
                await callback.message.edit_text(f"```json\n{response}\n```", parse_mode="Markdown")
            else:
                with open(filename, 'w') as f:
                    f.write(response)
                file = FSInputFile(filename, filename=os.path.basename(filename))
                await callback.message.answer_document(file)

        elif fmt == "text":
            text = format_as_table(rows)
            await callback.message.edit_text(f"```\n{text}\n```", parse_mode="Markdown")

        elif fmt == "markdown":
            md = format_as_table(rows, as_markdown=True)
            await callback.message.edit_text(f"```markdown\n{md}\n```", parse_mode="Markdown")

        elif fmt == "html":
            html = format_as_html(rows)
            with open(filename, 'w') as f:
                f.write(html)
            file = FSInputFile(filename, filename=os.path.basename(filename))
            await callback.message.answer_document(file)

        await callback.message.answer("Выбери таблицу:", reply_markup=get_table_kb())

    except Exception as e:
        await callback.message.edit_text(f"⚠️ Error: {str(e)}")
        await callback.message.answer("Выбери таблицу:", reply_markup=get_table_kb())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
