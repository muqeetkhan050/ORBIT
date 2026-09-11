from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from api.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GMAIL_REDIRECT_URI,
    GMAIL_SCOPES,
)
from api.database import SessionLocal
from api.models import Integration

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
FRONTEND_INBOX_URL = "http://localhost:3000/dashboard/inbox"
PROVIDER = "gmail"
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
        "redirect_uri": GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
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
            "redirect_uri": GMAIL_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    tokens = response.json()

    save_tokens(tokens)

    return RedirectResponse(f"{FRONTEND_INBOX_URL}?connected=true")


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


def extract_header(headers: list[dict], name: str) -> str:
    for header in headers:
        if header["name"] == name:
            return header["value"]
    return ""


def fetch_gmail_messages():
    tokens = load_tokens()
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    def auth_headers(access_token: str):
        return {"Authorization": f"Bearer {access_token}"}

    list_response = httpx.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers=auth_headers(tokens["access_token"]),
        params={"maxResults": 10},
    )

    if list_response.status_code == 401:
        tokens = refresh_access_token(tokens)
        list_response = httpx.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=auth_headers(tokens["access_token"]),
            params={"maxResults": 10},
        )

    list_response.raise_for_status()
    message_ids = [m["id"] for m in list_response.json().get("messages", [])]

    messages = []
    for message_id in message_ids:
        detail_response = httpx.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
            headers=auth_headers(tokens["access_token"]),
            params={
                "format": "metadata",
                "metadataHeaders": ["Subject", "From", "Date"],
            },
        )
        detail_response.raise_for_status()
        detail = detail_response.json()
        headers = detail.get("payload", {}).get("headers", [])

        messages.append(
            {
                "id": detail["id"],
                "subject": extract_header(headers, "Subject"),
                "from": extract_header(headers, "From"),
                "date": extract_header(headers, "Date"),
                "snippet": detail.get("snippet", ""),
            }
        )

    return messages


@router.get("/messages")
def get_messages():
    return fetch_gmail_messages()
