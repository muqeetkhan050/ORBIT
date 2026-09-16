from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from api.config import GEMINI_API_KEY
from api.gmail_tools import search_emails_tool

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=GEMINI_API_KEY)

checkpointer = InMemorySaver()

gmail_agent = create_react_agent(
    model,
    tools=[search_emails_tool],
    checkpointer=checkpointer,
)
