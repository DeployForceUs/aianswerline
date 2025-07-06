# Версия 1.0 (2025-07-05)
# ✅ Авторизация через Google

import os
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

load_dotenv("/opt/aianswerline/.env")

router = APIRouter()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # только для разработки

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPES = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"]

@router.get("/auth/login")
async def login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = REDIRECT_URI
    auth_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true")
    return RedirectResponse(auth_url)

@router.get("/auth/callback")
async def callback(request: Request):
    return {"status": "ok", "message": "🔐 Google Auth success (заглушка)"}
