from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth import get_current_user_id
from api.config import FRONTEND_URL
from api.gmail import router as gmail_router

from api.google_oauth import router as google_oauth_router
from api.agent import router as agent_router
from api.today import router as today_router
from api.tasks import router as tasks_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    google_oauth_router,
    prefix="/api/v1/integrations/google",
)


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/me")
def me(user_id: str = Depends(get_current_user_id)):
    """Returns the logged-in user's id. Used to check that login tokens work."""
    return {"user_id": user_id}


app.include_router(
    gmail_router,
    prefix="/api/v1/integrations/gmail",
)

app.include_router(
    agent_router,
    prefix="/api/v1/agent",
)

app.include_router(
    today_router,
    prefix="/api/v1/today",
)

app.include_router(
    tasks_router,
    prefix="/api/v1/tasks",
)

