from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.google_oauth import router as google_oauth_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
