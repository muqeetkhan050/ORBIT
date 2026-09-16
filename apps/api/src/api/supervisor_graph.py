from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from api.config import GEMINI_API_KEY
from api.supervisor_tools import calendar_agent_tool, gmail_agent_tool

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=GEMINI_API_KEY)

checkpointer = InMemorySaver()

supervisor_graph = create_react_agent(
    model,
    tools=[calendar_agent_tool, gmail_agent_tool],
    checkpointer=checkpointer,
)
