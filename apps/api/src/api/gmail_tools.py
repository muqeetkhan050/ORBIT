from langchain_core.tools import tool

from api.gmail import fetch_gmail_messages


@tool
def search_emails_tool() -> list:
    """Returns the user's recent Gmail messages (subject, sender, snippet, date).
    Use this whenever the user asks about their email or wants information found in their inbox.
    """
    return fetch_gmail_messages()
