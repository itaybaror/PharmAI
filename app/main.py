# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.intent import detect_intent

# FastAPI app entrypoint (this is what uvicorn loads)
app = FastAPI(title="PharmAI", version="0.0.1")



# Pull the most recent user message from the conversation (we route intent based on the latest user turn).
def get_last_user_message(conversation: list[dict]) -> str:
    for m in reversed(conversation):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


# Request schema for POST /chat (validated by Pydantic)
class ChatRequest(BaseModel):
    conversation: list[dict] = Field(default_factory=list)
    user_id: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat_route(payload: ChatRequest):
    # Stateless API: the client sends the conversation each call; we only need the latest user message to classify intent.
    last_user = get_last_user_message(payload.conversation)
    # LLM-based intent detection (returns a validated IntentDetection Pydantic model)
    intent = detect_intent(last_user)

    return {
        "assistant": f"Detected intent: {intent.intent}",
        "intent": intent.model_dump(),
    }