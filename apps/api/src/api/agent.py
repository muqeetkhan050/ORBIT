from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from api.config import GEMINI_API_KEY
from api.google_oauth import fetch_calendar_events
from api.gmail import fetch_gmail_messages
from api.calendar_tools import create_calendar_event_tool, delete_calendar_event_tool
from api.gmail_tools import search_emails_tool

router = APIRouter()

THREAD_ID = "default_thread"

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=GEMINI_API_KEY)

checkpointer = InMemorySaver()

agent_graph = create_react_agent(
    model,
    tools=[create_calendar_event_tool, delete_calendar_event_tool, search_emails_tool],
    checkpointer=checkpointer,
)


def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    return str(content)


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

    response = model.invoke(prompt)

    return {"briefing": extract_text(response.content)}


class ChatRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    approved: bool


def extract_result(result: dict) -> dict:
    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        return {
            "action": payload["action"],
            "params": payload["params"],
            "message": payload["message"],
        }

    final_message = result["messages"][-1].content
    return {"action": None, "message": extract_text(final_message)}


@router.post("/chat")
def chat(request: ChatRequest):
    today = datetime.now().strftime("%A, %Y-%m-%d")
    events = fetch_calendar_events()
    config = {"configurable": {"thread_id": THREAD_ID}}

    context = (
        f"Today is {today}.\n"
        f"Here are the user's upcoming calendar events (with their ids):\n{events}\n\n"
        f"User request: {request.message}"
    )

    result = agent_graph.invoke(
        {
            "messages": [
                {"role": "user", "content": context}
            ]
        },
        config=config,
    )

    return extract_result(result)


@router.post("/confirm")
def confirm(request: ConfirmRequest):
    config = {"configurable": {"thread_id": THREAD_ID}}
    decision = "approve" if request.approved else "reject"

    result = agent_graph.invoke(Command(resume=decision), config=config)

    return extract_result(result)
