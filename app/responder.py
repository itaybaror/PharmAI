# app/responder.py
import json
import os
import logging
from typing import Iterator

from openai import OpenAI

logger = logging.getLogger("app.responder")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


# Single source of truth for tool/workflow error codes -> meaning.
ERROR_HINTS: dict[str, str] = {
    "MISSING_USER_ID": "No user is selected.",
    "USER_NOT_FOUND": "The selected user does not exist in the demo database.",
    "MISSING_MEDICATION_QUERY": "No medication name was provided.",
    "MED_NOT_FOUND": "The medication was not found in the demo database.",
    "WORKFLOW_NOT_IMPLEMENTED": "That workflow is not implemented.",
    "CLINICIAN_GATE": "This depends on personal medical context and should be handled by a clinician.",
}


def stream_responder(context: dict) -> Iterator[str]:
    """
    One streaming LLM call that turns structured context into a natural reply.
    Must:
    - Respond in same language as the user's last message
    - Not invent facts (only use workflow_result/tool outputs)
    """
    ctx = dict(context or {})
    last_user = (ctx.get("last_user_message") or "").strip()
    intent = (ctx.get("intent") or {}).get("intent")
    wf = ctx.get("workflow_result") or {}
    ok = bool(wf.get("ok", True))
    code = wf.get("error_code")

    # Minimal, high-signal logs: start + (optional) error + done
    logger.info("responder_start intent=%r ok=%s code=%r", intent, ok, code)

    if code and "error_hints" not in ctx:
        ctx["error_hints"] = ERROR_HINTS

    instructions = (
        "You are PharmAI, a helpful pharmacy assistant.\n"
        "You will receive JSON context including:\n"
        "- last_user_message\n"
        "- intent\n"
        "- workflow_result (output produced by workflow handlers + tools)\n\n"
        "Rules:\n"
        "- Reply in the SAME language as last_user_message.\n"
        "- Be concise.\n"
        "- Use ONLY facts present in the context JSON.\n"
        "- If workflow_result.ok is false, use workflow_result.error_code and ERROR_HINTS to ask a short clarifying question.\n"
        "- Do not mention internal fields like 'error_code' or 'workflow_result'.\n"
        "- If the user asks about prescription requirement, answer only that.\n"
        "- Add a short safety disclaimer ONLY when discussing dosage/warnings/usage.\n"
    )

    user_content = "CONTEXT_JSON:\n" + json.dumps(ctx, ensure_ascii=False)

    emitted_any = False
    try:
        with client.responses.stream(
            model=MODEL,
            instructions=instructions,
            input=[{"role": "user", "content": user_content}],
        ) as stream:
            for event in stream:
                et = getattr(event, "type", "") or ""
                if et == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        emitted_any = True
                        yield delta
    except Exception:
        logger.exception("responder_error intent=%r ok=%s code=%r last_user=%r", intent, ok, code, last_user)
        raise
    finally:
        logger.info("responder_done intent=%r ok=%s code=%r emitted=%s", intent, ok, code, emitted_any)