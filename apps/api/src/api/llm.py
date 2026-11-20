from langchain_google_genai import ChatGoogleGenerativeAI

from api.config import GEMINI_API_KEY


model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=GEMINI_API_KEY,
    timeout=30,      # seconds to wait for one Gemini response
    max_retries=2,   # retry twice on network/overload errors, then give up
)
