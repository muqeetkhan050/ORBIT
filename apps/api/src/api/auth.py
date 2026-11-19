from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.config import OAUTH_STATE_SECRET, SUPABASE_URL

# Supabase publishes the PUBLIC keys it signs login tokens with at this URL.
# PyJWKClient downloads them once and caches them, so we don't fetch on every request.
jwks_client = jwt.PyJWKClient(
    f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json",
    cache_keys=True,
)

# Reads the "Authorization: Bearer <token>" header from the request.
# auto_error=False so we can return our own clear 401 message.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """FastAPI dependency: verifies the Supabase login token and returns the user's id.

    Add `user_id: str = Depends(get_current_user_id)` to any endpoint to require login.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    token = credentials.credentials

    try:
        # Find which of Supabase's public keys signed this token (by its "kid" header).
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Check the signature, expiry and audience. Any failure raises an error.
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Login expired, please log in again")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid login token")

    # "sub" (subject) is the user's unique id in Supabase, e.g. "3f1c...-..."
    return claims["sub"]


# ---------------------------------------------------------------------------
# OAuth "state": remembering WHO clicked "Connect" across Google's redirect.
#
# When Google redirects the browser back to /callback, that request carries no
# Authorization header, so get_current_user_id can't be used there. Instead,
# /connect puts the user id into a short-lived token signed with OUR secret,
# Google hands it back untouched as ?state=..., and /callback verifies it.
# Because it's signed, nobody can swap in another user's id.
# ---------------------------------------------------------------------------

STATE_LIFETIME = timedelta(minutes=10)


def create_oauth_state(user_id: str, provider: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "provider": provider, "iat": now, "exp": now + STATE_LIFETIME}
    return jwt.encode(payload, OAUTH_STATE_SECRET, algorithm="HS256")


def read_oauth_state(state: str, provider: str) -> str:
    """Returns the user id stored in the state, or raises 400 if it's invalid/expired."""
    try:
        payload = jwt.decode(state, OAUTH_STATE_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Connect link expired or invalid, please try again")

    if payload.get("provider") != provider:
        raise HTTPException(status_code=400, detail="State was issued for a different integration")

    return payload["sub"]
