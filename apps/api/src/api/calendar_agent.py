from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from api.config import GEMINI_API_KEY
from api.calendar_tools import (
    list_calendar_events_tool,
    create_calendar_event_tool,
    delete_calendar_event_tool,
)

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=GEMINI_API_KEY)

checkpointer = InMemorySaver()

calendar_agent = create_react_agent(
    model,
    tools=[list_calendar_events_tool, create_calendar_event_tool, delete_calendar_event_tool],
    checkpointer=checkpointer,
)
