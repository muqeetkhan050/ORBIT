import json
import os
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
from fastapi import HTTPException


from api.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    TOKENS_FILE,
)

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
FRONTEND_CALENDAR_URL = "http://localhost:3000/dashboard/calendar"


@router.get("/connect")
def connect():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/callback")
def callback(code: str):
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    tokens = response.json()

    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f)

    return RedirectResponse(f"{FRONTEND_CALENDAR_URL}?connected=true")


@router.get("/status")
def status():
    if not os.path.exists(TOKENS_FILE):
        return {"connected": False}

    with open(TOKENS_FILE) as f:
        tokens = json.load(f)

    return {"connected": "access_token" in tokens}


def refresh_access_token(tokens: dict) -> dict:
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": tokens["refresh_token"],
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    tokens.update(response.json())

    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f)

    return tokens


def fetch_calendar_events():
    if not os.path.exists(TOKENS_FILE):
        raise HTTPException(status_code=401, detail="Not connected")

    with open(TOKENS_FILE) as f:
        tokens = json.load(f)

    def fetch(access_token: str):
        return httpx.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "maxResults": 10,
                "orderBy": "startTime",
                "singleEvents": "true",
                "timeMin": datetime.now(timezone.utc).isoformat(),
            },
        )

    response = fetch(tokens["access_token"])

    if response.status_code == 401:
        tokens = refresh_access_token(tokens)
        response = fetch(tokens["access_token"])

    response.raise_for_status()
    return response.json().get("items", [])


@router.get("/events")
def get_events():
    return fetch_calendar_events()
