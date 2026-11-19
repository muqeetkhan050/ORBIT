import time

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import interrupt

from api.gmail import fetch_gmail_messages, send_gmail_message

# Emails sent recently: (user_id, to, subject, body) -> time sent.
# If a run crashes after sending and gets retried, the same approved email would
# be sent again. This guard makes sending idempotent for a short window.
RECENTLY_SENT: dict[tuple[str, str, str, str], float] = {}
DUPLICATE_WINDOW_SECONDS = 600


@tool
def search_emails_tool(config: RunnableConfig) -> list:
    """Returns the user's recent Gmail messages (subject, sender, snippet, date).
    Use this whenever the user asks about their email or wants information found in their inbox.
    """
    # user_id comes from LangGraph's config (set in agent.py from the login token).
    return fetch_gmail_messages(config["configurable"]["user_id"])


@tool
def send_email_tool(to: str, subject: str, body: str, config: RunnableConfig) -> str:
    """Sends an email from the user's Gmail account.
    `to` must be a full email address (e.g. ali@example.com), never just a name.
    Write the subject and body yourself based on what the user asked to say.
    """
    decision = interrupt(
        {
            "action": "send_email",
            "params": {"to": to, "subject": subject, "body": body},
            "message": f"I'll send this email to {to}:\n\nSubject: {subject}\n\n{body}\n\nSend it?",
        }
    )

    if decision != "approve":
        return "The user did not approve this email. Do not send it."

    user_id = config["configurable"]["user_id"]
    key = (user_id, to, subject, body)
    sent_at = RECENTLY_SENT.get(key)
    if sent_at and time.time() - sent_at < DUPLICATE_WINDOW_SECONDS:
        return f"This exact email to {to} was already sent a moment ago. Not sending a duplicate."

    send_gmail_message(user_id, to=to, subject=subject, body=body)
    RECENTLY_SENT[key] = time.time()
    return f"Sent the email to {to}."
