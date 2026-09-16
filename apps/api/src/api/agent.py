from fastapi import APIRouter
from pydantic import BaseModel

from langgraph.types import Command

from api.google_oauth import fetch_calendar_events
from api.gmail import fetch_gmail_messages
from api.supervisor_graph import model, supervisor_graph

router = APIRouter()

THREAD_ID = "default_thread"


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
    config = {"configurable": {"thread_id": THREAD_ID}}

    result = supervisor_graph.invoke(
        {
            "messages": [
                {"role": "user", "content": request.message}
            ]
        },
        config=config,
    )

    return extract_result(result)


@router.post("/confirm")
def confirm(request: ConfirmRequest):
    config = {"configurable": {"thread_id": THREAD_ID}}
    decision = "approve" if request.approved else "reject"

    result = supervisor_graph.invoke(Command(resume=decision), config=config)

    return extract_result(result)
