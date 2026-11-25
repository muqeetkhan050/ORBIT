from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from api.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    USER_TIMEZONE,
    FRONTEND_URL,
)
from api.database import SessionLocal
from api.models import Integration
from api.auth import create_oauth_state, get_current_user_id, read_oauth_state

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
FRONTEND_CALENDAR_URL = f"{FRONTEND_URL}/dashboard/calendar"
PROVIDER = "google_calendar"


def save_tokens(user_id: str, tokens: dict):
    db = SessionLocal()
    integration = (
        db.query(Integration)
        .filter_by(user_id=user_id, provider=PROVIDER)
        .first()
    )

    if integration:
        integration.access_token = tokens["access_token"]
        if "refresh_token" in tokens:
            integration.refresh_token = tokens["refresh_token"]
    else:
        integration = Integration(
            user_id=user_id,
            provider=PROVIDER,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
        )
        db.add(integration)

    db.commit()
    db.close()


def load_tokens(user_id: str):
    db = SessionLocal()
    integration = (
        db.query(Integration)
        .filter_by(user_id=user_id, provider=PROVIDER)
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
def connect(user_id: str = Depends(get_current_user_id)):
    # Called with apiFetch (login token attached). Returns the Google URL;
    # the signed "state" tells /callback which user this connection belongs to.
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": create_oauth_state(user_id, PROVIDER),
    }
    return {"url": f"{GOOGLE_AUTH_URL}?{urlencode(params)}"}


@router.get("/callback")
def callback(code: str, state: str):
    user_id = read_oauth_state(state, PROVIDER)
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

    save_tokens(user_id, tokens)

    return RedirectResponse(f"{FRONTEND_CALENDAR_URL}?connected=true")


@router.get("/status")
def status(user_id: str = Depends(get_current_user_id)):
    tokens = load_tokens(user_id)
    return {"connected": tokens is not None}


def refresh_access_token(user_id: str, tokens: dict) -> dict:
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

    save_tokens(user_id, tokens)

    return tokens


def fetch_calendar_events(
    user_id: str,
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    max_results: int = 10,
):
    tokens = load_tokens(user_id)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    # Defaults keep the old behaviour (next 10 events from now) for existing callers.
    params = {
        "maxResults": max_results,
        "orderBy": "startTime",
        "singleEvents": "true",  # expand repeating events into single occurrences
        "timeMin": (time_min or datetime.now(timezone.utc)).isoformat(),
    }
    if time_max:
        params["timeMax"] = time_max.isoformat()

    def fetch(access_token: str):
        return httpx.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )

    response = fetch(tokens["access_token"])

    if response.status_code == 401:
        tokens = refresh_access_token(user_id, tokens)
        response = fetch(tokens["access_token"])

    response.raise_for_status()
    return response.json().get("items", [])


def fetch_today_events(user_id: str) -> list[dict]:
    """All of today's events (midnight to midnight) in the user's time zone."""
    tz = ZoneInfo(USER_TIMEZONE)
    start_of_day = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    return fetch_calendar_events(
        user_id, time_min=start_of_day, time_max=end_of_day, max_results=50
    )


@router.get("/events")
def get_events(user_id: str = Depends(get_current_user_id)):
    return fetch_calendar_events(user_id)


def create_calendar_event(user_id: str, summary: str, start_datetime: str, end_datetime: str):
    tokens = load_tokens(user_id)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    body = {
        "summary": summary,
        "start": {"dateTime": start_datetime, "timeZone": USER_TIMEZONE},
        "end": {"dateTime": end_datetime, "timeZone": USER_TIMEZONE},
    }

    def post(access_token: str):
        return httpx.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            json=body,
        )

    response = post(tokens["access_token"])

    if response.status_code == 401:
        tokens = refresh_access_token(user_id, tokens)
        response = post(tokens["access_token"])

    response.raise_for_status()
    return response.json()

def delete_calendar_event(user_id: str, event_id: str):
    tokens = load_tokens(user_id)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    def delete(access_token: str):
        return httpx.delete(
            f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    response = delete(tokens["access_token"])

    if response.status_code == 401:
        tokens = refresh_access_token(user_id, tokens)
        response = delete(tokens["access_token"])

    response.raise_for_status()
    return {"deleted": event_id}
