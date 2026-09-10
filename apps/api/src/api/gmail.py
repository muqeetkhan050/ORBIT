import json
import os
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from api.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GMAIL_REDIRECT_URI,
    GMAIL_SCOPES,
    GMAIL_TOKENS_FILE,
)

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
FRONTEND_INBOX_URL = "http://localhost:3000/dashboard/inbox"


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

    with open(GMAIL_TOKENS_FILE, "w") as f:
        json.dump(tokens, f)

    return RedirectResponse(f"{FRONTEND_INBOX_URL}?connected=true")


@router.get("/status")
def status():
    if not os.path.exists(GMAIL_TOKENS_FILE):
        return {"connected": False}

    with open(GMAIL_TOKENS_FILE) as f:
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

    with open(GMAIL_TOKENS_FILE, "w") as f:
        json.dump(tokens, f)

    return tokens


def extract_header(headers: list[dict], name: str) -> str:
    for header in headers:
        if header["name"] == name:
            return header["value"]
    return ""


def fetch_gmail_messages():
    if not os.path.exists(GMAIL_TOKENS_FILE):
        raise HTTPException(status_code=401, detail="Not connected")

    with open(GMAIL_TOKENS_FILE) as f:
        tokens = json.load(f)

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
