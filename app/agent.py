# app/agent.py
import logging

from app.intent import detect_intent
from app.schemas import ChatRequest
from app.workflows import ROUTES

logger = logging.getLogger("app.agent")


def get_last_user_message(conversation: list[dict]) -> str:
    """Return the most recent user message content (or "" if none)."""
    for m in reversed(conversation):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


def handle_chat(payload: ChatRequest) -> dict:
    """Detect intent for the latest user message, apply clinician gate, then route to a workflow."""
    last_user = get_last_user_message(payload.conversation)
    logger.info("handle_chat conversation_len=%s last_user=%r", len(payload.conversation), last_user)

    intent = detect_intent(last_user)
    logger.info(
        "intent=%s confidence=%.2f med_query=%r med_info_type=%s needs_clinician=%s",
        getattr(intent, "intent", None),
        getattr(intent, "confidence", 0.0),
        getattr(intent, "medication_query", None),
        getattr(intent, "med_info_type", None),
        getattr(intent, "needs_clinician", None),
    )

    # Global safety gate: even if intent is UNKNOWN, redirect if the question requires a clinician
    if getattr(intent, "needs_clinician", False):
        reason = (getattr(intent, "clinician_reason", "") or "").strip()
        logger.warning(
            "clinician_gate_hit intent=%s confidence=%.2f reason=%r last_user=%r",
            getattr(intent, "intent", None),
            getattr(intent, "confidence", 0.0),
            reason,
            last_user,
        )
        msg = reason if reason else "This question may depend on personal medical context."
        return {
            "assistant": msg + "\n\nFor personal medical advice, consult a healthcare professional.",
            "intent": intent.model_dump(),
        }

    handler = ROUTES.get(getattr(intent, "intent", ""))
    if handler:
        return handler(intent, last_user, payload.conversation)

    return {
        "assistant": f"Detected intent: {intent.intent} (workflow not implemented yet)",
        "intent": intent.model_dump(),
    }