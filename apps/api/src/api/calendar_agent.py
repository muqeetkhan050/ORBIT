from api.llm import model
from api.memory import checkpointer
from langgraph.prebuilt import create_react_agent

from api.calendar_tools import (
    list_calendar_events_tool,
    create_calendar_event_tool,
    delete_calendar_event_tool,
)


calendar_agent = create_react_agent(
    model,
    tools=[list_calendar_events_tool, create_calendar_event_tool, delete_calendar_event_tool],
    checkpointer=checkpointer,
)
