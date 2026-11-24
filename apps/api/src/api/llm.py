from langchain_google_genai import ChatGoogleGenerativeAI

from api.config import GEMINI_API_KEY


model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=GEMINI_API_KEY,
    # Sent to Google as a server deadline (X-Server-Timeout). 30s was too tight:
    # under load Google cancelled requests with 504 DEADLINE_EXCEEDED.
    timeout=60,      # seconds to wait for one Gemini response
    max_retries=2,   # retry twice on network/overload errors, then give up
    # Gemini "thinks" before answering. Our tasks (pick an agent, call a tool) are
    # simple, so low thinking is about 2x faster and uses far fewer tokens.
    thinking_config={"thinking_level": "low"},
)
