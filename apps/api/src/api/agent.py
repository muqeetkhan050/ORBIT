

from google import genai
from fastapi import APIRouter
from fastapi import HTTPException                              # ← ADD
from datetime import datetime                                    # ← ADD
from google.genai import types                                   # ← ADD
from pydantic import BaseModel                                   # ← ADD

from api.config import GEMINI_API_KEY
from api.google_oauth import fetch_calendar_events, create_calendar_event   # ← MODIFY (add create_calendar_event)
from api.gmail import fetch_gmail_messages

router = APIRouter()

client = genai.Client(api_key=GEMINI_API_KEY)

# ↓↓↓ ADD all of this new block here, between `client = ...` and `@router.get("/briefing")` ↓↓↓

class ChatRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    action: str
    params: dict


create_event_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="create_calendar_event",
            description="Creates a new event on the user's Google Calendar.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "summary": types.Schema(type="STRING", description="Short title of the event"),
                    "start_datetime": types.Schema(type="STRING", description="Start date and time in ISO 8601 format, e.g. 2026-09-13T09:00:00"),
                    "end_datetime": types.Schema(type="STRING", description="End date and time in ISO 8601 format"),
                },
                required=["summary", "start_datetime", "end_datetime"],
            ),
        )
    ]
)




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
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return {"briefing": response.text}


# ↓↓↓ ADD both of these new routes here, AFTER get_briefing(), at the end of the file ↓↓↓

@router.post("/chat")
def chat(request: ChatRequest):
    today = datetime.now().strftime("%A, %Y-%m-%d")

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Today is {today}. User request: {request.message}",
        config=types.GenerateContentConfig(tools=[create_event_tool]),
    )

    part = response.candidates[0].content.parts[0]

    if part.function_call:
        params = dict(part.function_call.args)
        return {
            "action": "create_calendar_event",
            "params": params,
            "message": f"I'll create \"{params['summary']}\" from {params['start_datetime']} to {params['end_datetime']}. Confirm?",
        }

    return {"action": None, "message": response.text}


@router.post("/confirm")
def confirm(request: ConfirmRequest):
    if request.action == "create_calendar_event":
        create_calendar_event(
            summary=request.params["summary"],
            start_datetime=request.params["start_datetime"],
            end_datetime=request.params["end_datetime"],
        )
        return {"message": f"Done — added \"{request.params['summary']}\" to your calendar."}

    raise HTTPException(status_code=400, detail="Unknown action")
