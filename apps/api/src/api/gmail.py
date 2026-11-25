import base64
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from api.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GMAIL_REDIRECT_URI,
    GMAIL_SCOPES,
    FRONTEND_URL,
)
from api.database import SessionLocal
from api.models import Integration
from api.auth import create_oauth_state, get_current_user_id, read_oauth_state

router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
FRONTEND_INBOX_URL = f"{FRONTEND_URL}/dashboard/inbox"
PROVIDER = "gmail"



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
    # Called by the frontend with apiFetch (so we know who is logged in).
    # Returns the Google URL instead of redirecting; the browser then goes there.
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        # Google sends this back unchanged to /callback, so we know whose tokens they are.
        "state": create_oauth_state(user_id, PROVIDER),
    }
    return {"url": f"{GOOGLE_AUTH_URL}?{urlencode(params)}"}


@router.get("/callback")
def callback(code: str, state: str):
    # Check the state BEFORE using the code, so a forged request is rejected early.
    user_id = read_oauth_state(state, PROVIDER)

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

    save_tokens(user_id, tokens)

    return RedirectResponse(f"{FRONTEND_INBOX_URL}?connected=true")


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


def extract_header(headers: list[dict], name: str) -> str:
    for header in headers:
        if header["name"] == name:
            return header["value"]
    return ""


def fetch_gmail_messages(user_id: str, query: str | None = None, max_results: int = 10):
    tokens = load_tokens(user_id)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    def auth_headers(access_token: str):
        return {"Authorization": f"Bearer {access_token}"}

    # Built once so the first call and the retry after a token refresh
    # always ask Gmail for the same emails.
    list_params = {"maxResults": max_results}
    if query:
        list_params["q"] = query  # same syntax as the Gmail search box

    list_response = httpx.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers=auth_headers(tokens["access_token"]),
        params=list_params,
    )

    if list_response.status_code == 401:
        tokens = refresh_access_token(user_id, tokens)
        list_response = httpx.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=auth_headers(tokens["access_token"]),
            params=list_params,
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


def fetch_recent_emails(user_id: str, hours: int = 48) -> list[dict]:
    """Inbox emails from the last `hours` hours, without promotions/social noise."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = f"in:inbox after:{int(since.timestamp())} -category:promotions -category:social"
    return fetch_gmail_messages(user_id, query=query, max_results=30)






def send_gmail_message(user_id: str, to: str, subject: str, body: str) -> dict:
    tokens = load_tokens(user_id)
    if tokens is None:
        raise HTTPException(status_code=401, detail="Not connected")

    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    def post(access_token: str):
        return httpx.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
        )

    response = post(tokens["access_token"])
    if response.status_code == 401:
        tokens = refresh_access_token(user_id, tokens)
        response = post(tokens["access_token"])

    response.raise_for_status()
    return response.json()


@router.get("/messages")
def get_messages(user_id: str = Depends(get_current_user_id)):
    return fetch_gmail_messages(user_id)
