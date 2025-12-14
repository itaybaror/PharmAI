# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.intent import detect_intent

app = FastAPI(title="PharmAI", version="0.0.1")


class ChatRequest(BaseModel):
    conversation: list[dict] = Field(default_factory=list)
    user_id: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat_route(payload: ChatRequest):
    last_user = next(
        (m.get("content") for m in reversed(payload.conversation) if m.get("role") == "user"),
        "",
    )
    intent = detect_intent(last_user)

    return {
        "assistant": f"Detected intent: {intent.intent}",
        "intent": intent.model_dump(),
    }