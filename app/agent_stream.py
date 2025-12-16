# app/agent_stream.py
# New approach:
# 1) Intent LLM call (detect_intent)
# 2) Workflow handler -> tools (returns structured result; no assistant prose)
# 3) Responder LLM streaming call (final user-facing answer, same language as user)

import os
import json
import logging
from typing import Iterator

from openai import OpenAI

from app.schemas import ChatRequest
from app.intent import detect_intent
from app.workflows import ROUTES
from app.error_codes import hint_for

logger = logging.getLogger("app.agent_stream")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _last_user_message(conversation: list[dict]) -> str:
    for m in reversed(conversation or []):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


def stream_chat(payload: ChatRequest) -> Iterator[str]:
    yield _sse("start", {"ok": True})

    try:
        conversation = payload.conversation or []
        last_user = _last_user_message(conversation)

        # 1) Intent
        intent = detect_intent(conversation)

        # 2) Handler -> tools (structured result, no assistant prose)
        if getattr(intent, "needs_clinician", False):
            reason = (getattr(intent, "clinician_reason", "") or "").strip()
            workflow_result = {
                "ok": False,
                "type": "clinician_gate",
                "error_code": "NEEDS_CLINICIAN",
                "reason": reason or "This question may depend on personal medical context.",
            }
        else:
            handler = ROUTES.get(getattr(intent, "intent", "") or "")
            if not handler:
                workflow_result = {
                    "ok": False,
                    "type": "router",
                    "error_code": "NO_HANDLER",
                    "intent": getattr(intent, "intent", "UNKNOWN"),
                }
            else:
                workflow_result = handler(intent, last_user, conversation, payload.user_id)

        # 3) Streaming responder: turn {intent + workflow_result} into a final answer
        error_code = workflow_result.get("error_code") if isinstance(workflow_result, dict) else None
        error_hint = hint_for(error_code)

        instructions = (
            "You are PharmAI, a helpful pharmacy assistant.\n"
            "You will receive a JSON context with:\n"
            "- last_user_message\n"
            "- intent (structured)\n"
            "- workflow_result (structured; produced by code calling tools)\n\n"
            "Rules:\n"
            "- Respond in the SAME language as last_user_message.\n"
            "- Be concise and conversational.\n"
            "- Use ONLY facts present in workflow_result (and intent if needed). Do not invent data.\n"
            "- If workflow_result.ok is false: follow the provided error_hint and ask at most one clarifying question.\n"
            "- If error_code is NEEDS_CLINICIAN: give a brief safety response and recommend a clinician.\n"
        )

        context_obj = {
            "last_user_message": last_user,
            "intent": intent.model_dump(),
            "workflow_result": workflow_result,
            "error_hint": error_hint,
        }

        with client.responses.stream(
            model=MODEL,
            instructions=instructions,
            input=[{"role": "user", "content": json.dumps(context_obj, ensure_ascii=False)}],
        ) as stream:
            for event in stream:
                et = getattr(event, "type", "") or ""

                if et == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        yield _sse("delta", {"text": delta})

            final_text = ""
            try:
                final_text = stream.get_final_response().output_text or ""
            except Exception:
                pass

            yield _sse("done", {"ok": True, "text": final_text})

    except Exception as e:
        logger.exception("stream_chat error")
        yield _sse("error", {"message": str(e)})
        yield _sse("done", {"ok": False})