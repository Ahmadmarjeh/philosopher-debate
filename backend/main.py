import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from .debate import run_debate
except ImportError:
    from debate import run_debate


app = FastAPI()
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
frontend_origin = os.getenv("FRONTEND_ORIGIN")
if frontend_origin:
    allowed_origins.append(frontend_origin.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DebateRequest(BaseModel):
    question: str
    rounds: int = Field(default=1, ge=1, le=3)


@app.post("/debate")
def debate(request: DebateRequest):
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    try:
        result = run_debate(request.question.strip(), request.rounds)
    except Exception as error:
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="No AI API key is configured. Add GROQ_API_KEY to backend/.env.",
            ) from error
        if getattr(error, "status_code", None) == 429:
            raise HTTPException(
                status_code=402,
                detail="The AI provider rate limit or free-tier quota was reached. Try again later or check your provider account.",
            ) from error
        if getattr(error, "status_code", None) == 413:
            raise HTTPException(
                status_code=413,
                detail="The debate context is too large for the provider's free tier. Use a shorter question or fewer rounds.",
            ) from error
        if error.__class__.__name__ == "APITimeoutError":
            raise HTTPException(
                status_code=504,
                detail="The AI provider took too long to answer. Try one round or submit the debate again.",
            ) from error
        if getattr(error, "status_code", None) == 401:
            raise HTTPException(
                status_code=502,
                detail="The AI provider rejected the API key. Create a new key and update backend/.env.",
            ) from error
        if "empty response" in str(error).lower():
            raise HTTPException(
                status_code=502,
                detail="The AI provider returned an empty answer. Please try the debate again.",
            ) from error
        raise

    return {
        "question": request.question,
        "debate": result
    }


frontend_directory = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")