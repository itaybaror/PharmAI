# app/agent.py
import logging

from app.intent import detect_intent
from app.schemas import ChatRequest
from app.workflows import ROUTES

logger = logging.getLogger("app.agent")


def get_last_user_message(conversation: list[dict]) -> str:
    for m in reversed(conversation):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


def handle_chat(payload: ChatRequest) -> dict:
    last_user = get_last_user_message(payload.conversation)
    logger.info("handle_chat conversation_len=%s last_user=%r", len(payload.conversation), last_user)

    intent = detect_intent(last_user)
    logger.info(
        "intent=%s confidence=%.2f med_query=%r",
        getattr(intent, "intent", None),
        getattr(intent, "confidence", 0.0),
        getattr(intent, "medication_query", None),
    )

    handler = ROUTES.get(getattr(intent, "intent", ""))
    if handler:
        return handler(intent, last_user, payload.conversation)

    return {
        "assistant": f"Detected intent: {intent.intent} (workflow not implemented yet)",
        "intent": intent.model_dump(),
    }