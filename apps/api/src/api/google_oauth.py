from urllib.parse import urlencode
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from api.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
)
from api.database import SessionLocal
from api.models import Integration

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
FRONTEND_CALENDAR_URL = "http://localhost:3000/dashboard/calendar"
PROVIDER = "google_calendar"
USER_ID = "default_user"


def save_tokens(tokens: dict):
    db = SessionLocal()
    integration = (
        db.query(Integration)
        .filter_by(user_id=USER_ID, provider=PROVIDER)
        .first()
    )

    if integration:
        integration.access_token = tokens["access_token"]
        if "refresh_token" in tokens:
            integration.refresh_token = tokens["refresh_token"]
    else:
        integration = Integration(
            user_id=USER_ID,
            provider=PROVIDER,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
        )
        db.add(integration)

    db.commit()
    db.close()


def load_tokens():
    db = SessionLocal()
    integration = (
        db.query(Integration)
        .filter_by(user_id=USER_ID, provider=PROVIDER)
        .first()
    )
    db.close()

    if not integration:
        return None

    return {
        "access_token": integration.access_token,
        "refresh_token": integration.refresh_token,
    }


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

    save_tokens(tokens)

    return RedirectResponse(f"{FRONTEND_CALENDAR_URL}?connected=true")


@router.get("/status")
def status():
    tokens = load_tokens()
    return {"connected": tokens is not None}


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

    save_tokens(tokens)

    return tokens


def fetch_calendar_events():
    tokens = load_tokens()
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

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


def create_calendar_event(summary: str, start_datetime: str, end_datetime: str):
    tokens = load_tokens()
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    body = {
        "summary": summary,
        "start": {"dateTime": start_datetime, "timeZone": "Australia/Brisbane"},
        "end": {"dateTime": end_datetime, "timeZone": "Australia/Brisbane"},
    }

    def post(access_token: str):
        return httpx.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            json=body,
        )

    response = post(tokens["access_token"])

    if response.status_code == 401:
        tokens = refresh_access_token(tokens)
        response = post(tokens["access_token"])

    response.raise_for_status()
    return response.json()

def delete_calendar_event(event_id: str):
    tokens = load_tokens()
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    def delete(access_token: str):
        return httpx.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    response = delete(tokens["access_token"])

    if response.status_code == 401:
        tokens = refresh_access_token(tokens)
        response = delete(tokens["access_token"])

    response.raise_for_status()
    return {"deleted": event_id}
