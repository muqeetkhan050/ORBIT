from fastapi import APIRouter
from pydantic import BaseModel

from langgraph.types import Command

from api.google_oauth import fetch_calendar_events
from api.gmail import fetch_gmail_messages
from api.supervisor_graph import model, supervisor_graph
from api.gmail_agent import gmail_agent
from api.calendar_agent import calendar_agent
from api.supervisor_tools import GMAIL_THREAD_ID, CALENDAR_THREAD_ID

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


def reset_conversation():
    """Wipe the saved state of the supervisor and both sub-agents.

    Used after a crash. A run that fails partway (e.g. Gemini 429 right after an
    email was sent) leaves the graphs looking "paused". If we kept that state,
    the next Confirm click would replay the run and send the email again.
    """
    supervisor_graph.checkpointer.delete_thread(THREAD_ID)
    gmail_agent.checkpointer.delete_thread(GMAIL_THREAD_ID)
    calendar_agent.checkpointer.delete_thread(CALENDAR_THREAD_ID)


def error_response(error: Exception) -> dict:
    reset_conversation()
    if "RESOURCE_EXHAUSTED" in str(error) or "429" in str(error):
        reason = "the Gemini API quota is used up for now"
    else:
        reason = f"{type(error).__name__}"
    return {
        "action": None,
        "error": True,
        "message": (
            f"Something went wrong ({reason}). I've reset the conversation. "
            "If you just confirmed an email, check your Sent folder before trying again."
        ),
    }


def has_pending_approval(config: dict) -> bool:
    state = supervisor_graph.get_state(config)
    return any(task.interrupts for task in state.tasks)


@router.post("/chat")
def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": THREAD_ID}}

    try:
        # If an action is still waiting for Confirm/Cancel, the paused tool call has
        # no result yet. Adding a new message on top would break the chat history,
        # so treat a new message as "Cancel" for the pending action first.
        if has_pending_approval(config):
            supervisor_graph.invoke(Command(resume="reject"), config=config)

        result = supervisor_graph.invoke(
            {
                "messages": [
                    {"role": "user", "content": request.message}
                ]
            },
            config=config,
        )
        return extract_result(result)
    except Exception as error:
        return error_response(error)


@router.post("/confirm")
def confirm(request: ConfirmRequest):
    config = {"configurable": {"thread_id": THREAD_ID}}
    decision = "approve" if request.approved else "reject"

    # Nothing waiting for approval (e.g. a double click, or state was reset):
    # do nothing instead of replaying an old run.
    if not has_pending_approval(config):
        return {"action": None, "message": "There's nothing waiting for confirmation."}

    try:
        result = supervisor_graph.invoke(Command(resume=decision), config=config)
        return extract_result(result)
    except Exception as error:
        return error_response(error)
