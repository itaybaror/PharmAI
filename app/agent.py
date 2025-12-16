# app/agent.py
import json
import logging
from typing import Iterator

from app.intent import detect_intent
from app.schemas import ChatRequest
from app.workflows import ROUTES
from app.responder import stream_responder

logger = logging.getLogger("app.agent")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def get_last_user_message(conversation: list[dict]) -> str:
    """Return the most recent user message content (or '' if none)."""
    for m in reversed(conversation or []):
        if m.get("role") == "user":
            return str(m.get("content") or "").strip()
    return ""


def _run_workflow(intent, payload: ChatRequest) -> dict:
    """Call the selected workflow handler. Workflow should call tools and return structured data."""
    last_user = get_last_user_message(payload.conversation)
    handler = ROUTES.get(getattr(intent, "intent", ""))

    if not handler:
        return {
            "ok": False,
            "error_code": "WORKFLOW_NOT_IMPLEMENTED",
            "intent": getattr(intent, "intent", "UNKNOWN"),
        }

    return handler(intent, last_user, payload.conversation, payload.user_id)


def stream_chat(payload: ChatRequest) -> Iterator[str]:
    """
    SSE stream:
    1) intent (LLM parse, non-stream)
    2) workflow handler (tools)
    3) responder (LLM stream)
    """
    yield _sse("start", {"ok": True})

    try:
        last_user = get_last_user_message(payload.conversation)
        logger.info("stream_chat conversation_len=%s user_id=%r last_user=%r", len(payload.conversation), payload.user_id, last_user)

        intent = detect_intent(payload.conversation)
        logger.info(
            "intent=%s confidence=%.2f med_query=%r med_info_type=%s needs_clinician=%s",
            getattr(intent, "intent", None),
            getattr(intent, "confidence", 0.0),
            getattr(intent, "medication_query", None),
            getattr(intent, "med_info_type", None),
            getattr(intent, "needs_clinician", None),
        )

        # Global safety gate (still part of orchestration)
        if getattr(intent, "needs_clinician", False):
            reason = (getattr(intent, "clinician_reason", "") or "").strip()
            workflow_result = {
                "ok": False,
                "error_code": "CLINICIAN_GATE",
                "message": reason or "This question may depend on personal medical context.",
            }
        else:
            workflow_result = _run_workflow(intent, payload)

        context = {
            "last_user_message": last_user,
            "user_id": payload.user_id,
            "intent": intent.model_dump(),
            "workflow_result": workflow_result,
        }

        for delta in stream_responder(context):
            yield _sse("delta", {"text": delta})

        yield _sse("done", {"ok": True})

    except Exception as e:
        logger.exception("stream_chat error")
        yield _sse("error", {"message": str(e)})
        yield _sse("done", {"ok": False})