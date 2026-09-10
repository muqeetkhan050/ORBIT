from google import genai
from fastapi import APIRouter

from api.config import GEMINI_API_KEY
from api.google_oauth import fetch_calendar_events
from api.gmail import fetch_gmail_messages

router = APIRouter()

client = genai.Client(api_key=GEMINI_API_KEY)


@router.get("/briefing")
def get_briefing():
    events = fetch_calendar_events()
    messages = fetch_gmail_messages()

    prompt = (
        "Here are my upcoming calendar events and recent emails.\n\n"
        f"Calendar events:\n{events}\n\n"
        f"Recent emails:\n{messages}\n\n"
        "Summarize what needs my attention today in a short, clear briefing."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return {"briefing": response.text}
