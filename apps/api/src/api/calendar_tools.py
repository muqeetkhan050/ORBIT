from langchain_core.tools import tool
from langgraph.types import interrupt

from api.google_oauth import create_calendar_event, delete_calendar_event


@tool
def create_calendar_event_tool(summary: str, start_datetime: str, end_datetime: str) -> str:
    """Creates a new event on the user's Google Calendar.
    start_datetime and end_datetime must be ISO 8601 format, e.g. 2026-09-13T09:00:00.
    """
    decision = interrupt(
        {
            "action": "create_calendar_event",
            "params": {
                "summary": summary,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
            },
            "message": f"I'll create \"{summary}\" from {start_datetime} to {end_datetime}. Confirm?",
        }
    )

    if decision != "approve":
        return "The user did not approve this action. Do not create the event."

    create_calendar_event(
        summary=summary, start_datetime=start_datetime, end_datetime=end_datetime
    )
    return f"Created the event '{summary}'."


@tool
def delete_calendar_event_tool(event_id: str) -> str:
    """Deletes or cancels an existing event on the user's Google Calendar, given its event id."""
    decision = interrupt(
        {
            "action": "delete_calendar_event",
            "params": {"event_id": event_id},
            "message": "I'll delete that event. Confirm?",
        }
    )

    if decision != "approve":
        return "The user did not approve this action. Do not delete the event."

    delete_calendar_event(event_id=event_id)
    return "Deleted the event."
