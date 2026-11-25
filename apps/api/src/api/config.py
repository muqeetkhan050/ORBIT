import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.events",
]

GMAIL_REDIRECT_URI = os.environ["GMAIL_REDIRECT_URI"]

GMAIL_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

DATABASE_URL = os.environ["DATABASE_URL"]

SUPABASE_URL = os.environ["SUPABASE_URL"]

# Where the website runs. localhost on your laptop; the Vercel address after deploying.
# os.environ[...] (not .get) so a missing value crashes at startup with a clear error.
FRONTEND_URL = os.environ["FRONTEND_URL"]

# Time zone for calendar events and for telling the agent what "today" is.
# One value for now; later this should come from each user's settings.
USER_TIMEZONE = "Australia/Brisbane"

# Secret used to sign the OAuth "state" parameter (see auth.py).
OAUTH_STATE_SECRET = os.environ["OAUTH_STATE_SECRET"]
