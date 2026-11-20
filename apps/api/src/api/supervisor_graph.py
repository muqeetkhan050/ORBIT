from api.llm import model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from api.supervisor_tools import calendar_agent_tool, gmail_agent_tool


checkpointer = InMemorySaver()

supervisor_graph = create_react_agent(
    model,
    tools=[calendar_agent_tool, gmail_agent_tool],
    checkpointer=checkpointer,
)
