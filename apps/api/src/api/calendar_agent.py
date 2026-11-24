from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

from api.config import USER_TIMEZONE
from api.llm import model
from api.memory import checkpointer
from api.calendar_tools import (
    list_calendar_events_tool,
    create_calendar_event_tool,
    delete_calendar_event_tool,
)


def calendar_prompt(state):
    """Builds the system prompt on EVERY model call, so "today" is always current.

    The model has no clock. Without this it guesses the date (it once picked the
    date of the next upcoming event and booked "today at 3pm" on the wrong day).
    """
    now = datetime.now(ZoneInfo(USER_TIMEZONE))
    system = (
        "You are the user's calendar assistant.\n"
        f"Right now it is {now:%A, %d %B %Y, %H:%M} in the user's time zone ({USER_TIMEZONE}).\n"
        f"Today's date is {now:%Y-%m-%d}. Work out 'today', 'tomorrow', 'next Monday' etc. from this date, "
        "never from the dates of existing events.\n"
        "- Datetimes you pass to tools are local times in the user's time zone, "
        "ISO 8601 without an offset, e.g. 2026-09-13T15:00:00.\n"
        "- If no duration is given, make the event 1 hour long.\n"
        "- If no title is given, use a short sensible one like 'Meeting'.\n"
        "- To create or delete an event, call the tool right away. Don't ask the user to confirm in text; "
        "the tool asks for approval itself."
    )
    return [SystemMessage(content=system)] + state["messages"]


calendar_agent = create_react_agent(
    model,
    tools=[list_calendar_events_tool, create_calendar_event_tool, delete_calendar_event_tool],
    prompt=calendar_prompt,
    checkpointer=checkpointer,
)
