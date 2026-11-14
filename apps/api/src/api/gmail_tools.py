from langchain_core.tools import tool

from api.gmail import fetch_gmail_messages

from langgraph.types import interrupt

from api.gmail import fetch_gmail_messages, send_gmail_message


@tool
def search_emails_tool() -> list:
    """Returns the user's recent Gmail messages (subject, sender, snippet, date).
    Use this whenever the user asks about their email or wants information found in their inbox.
    """
    return fetch_gmail_messages()



# ... search_emails_tool stays the same ...


@tool
def send_email_tool(to: str, subject: str, body: str) -> str:
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

    send_gmail_message(to=to, subject=subject, body=body)
    return f"Sent the email to {to}."

