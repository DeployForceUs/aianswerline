# Версия 2.1 (2025-07-05)
# ✅ Использует APIRouter
# ✅ GET /addtokens/{phone} → редирект на Square
# ✅ POST /addtokens → (заглушка)
# ✅ Готово к расширению логики

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
SQUARE_LINK_BASE = "https://square.link/u/RjeggMHg"

@router.get("/{phone}")
async def redirect_to_square(phone: str):
    square_link = f"{SQUARE_LINK_BASE}?ref={phone}"
    return RedirectResponse(url=square_link)

@router.post("/")
async def add_tokens(request: Request):
    data = await request.json()
    print("[ADD TOKENS POST] 📦", data)
    return {"status": "ok", "message": "POST endpoint placeholder"}
