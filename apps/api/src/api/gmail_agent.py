from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from api.config import GEMINI_API_KEY
from api.gmail_tools import search_emails_tool, send_email_tool

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=GEMINI_API_KEY)


GMAIL_AGENT = '''You are the user's email assistant.
- To send an email you need the recipient's full email address.
- If the user only gives a name, use search_emails_tool to find that person's address
  in recent emails. If you can't find it, ask the user for it. Never invent an address.
- Write short, polite emails in the user's voice. Don't add placeholders like [Your Name].
- Once you have the address, call send_email_tool right away. Don't ask the user to confirm
  in text: the tool itself shows the user the draft with a Confirm button before sending.'''


checkpointer = InMemorySaver()

gmail_agent = create_react_agent(
    model,
    tools=[search_emails_tool, send_email_tool],
    prompt=GMAIL_AGENT,
    checkpointer=checkpointer,
)
