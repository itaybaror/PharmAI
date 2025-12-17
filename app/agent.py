# app/agent.py
import os
import json
import logging
from typing import Iterator, Any

from openai import OpenAI

from app.schemas import ChatRequest
from app import tools as local_tools  # your app/tools.py module

logger = logging.getLogger("app.agent")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _get_last_user_message(conversation: list[dict]) -> str:
    for m in reversed(conversation or []):
        if (m.get("role") or "").lower() == "user":
            return str(m.get("content") or "").strip()
    return ""


# ----------------------------
# Tool schemas (Responses API)
# IMPORTANT: top-level "name" is REQUIRED (NOT nested under "function")
# ----------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_medication",
        "description": "Fetch factual medication info (label facts), prescription requirement, and stock from the demo DB.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Medication name, brand, or alias (free text)."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_user_prescriptions",
        "description": "List a demo user's prescriptions (resolved to medication summaries) from the demo DB.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Demo user id like 'u001'."},
            },
            "required": ["user_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_user_prescription",
        "description": "Check if a demo user has a prescription for a medication in the demo DB.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Demo user id like 'u001'."},
                "medication_query": {"type": "string", "description": "Medication name, brand, or alias (free text)."},
            },
            "required": ["user_id", "medication_query"],
            "additionalProperties": False,
        },
    },
]


# Map tool name -> python callable (must match TOOLS[*].name exactly)
TOOL_IMPL = {
    "get_medication": local_tools.get_medication,
    "get_user_prescriptions": local_tools.get_user_prescriptions,
    "check_user_prescription": local_tools.check_user_prescription,
}


def stream_chat(payload: ChatRequest) -> Iterator[str]:
    """
    Single streaming LLM call with tool calling enabled.
    Notes:
    - DO NOT use previous_response_id (your org has Zero Data Retention) -> always send conversation each time.
    - Tools are defined in this file with the correct Responses API schema (top-level name).
    """
    yield _sse("start", {"ok": True})

    # Quick sanity check for the exact error you saw ("tools[0].name" missing)
    if not TOOLS or not TOOLS[0].get("name"):
        yield _sse("error", {"message": "Internal error: tool schema missing top-level name."})
        yield _sse("done", {"ok": False})
        return

    last_user = _get_last_user_message(payload.conversation)
    logger.info("stream_chat conversation_len=%s user_id=%r last_user=%r", len(payload.conversation or []), payload.user_id, last_user)

    instructions = (
        "You are PharmAI, a helpful pharmacy assistant.\n"
        "You have access to tools for a small demo database.\n"
        "Rules:\n"
        "- Use tools when you need DB facts (med info, stock, prescriptions).\n"
        "- Do not invent medication facts or user data.\n"
        "- If user asks for medical advice (personalized suitability/diagnosis/interactions), recommend consulting a clinician.\n"
        "- Respond in the same language as the user.\n"
        "- Be concise.\n"
    )

    # Convert your stored conversation to Responses API input messages.
    # Keep it simple: only pass user/assistant roles with content.
    input_msgs: list[dict] = []
    for m in (payload.conversation or []):
        role = (m.get("role") or "").lower().strip()
        content = str(m.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            input_msgs.append({"role": role, "content": content})

    try:
        with client.responses.stream(
            model=MODEL,
            instructions=instructions,
            input=input_msgs,
            tools=TOOLS,
            tool_choice="auto",
            store=False,
        ) as stream:
            # The Responses streaming event surface can differ slightly by SDK version.
            # We handle the two essentials:
            # 1) text deltas
            # 2) tool calls (function_call items)
            pending_calls: dict[str, dict] = {}

            for event in stream:
                et = getattr(event, "type", "") or ""

                # 1) Stream assistant text
                if et == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        yield _sse("delta", {"text": delta})
                    continue

                # 2) Detect tool calls (common pattern: output_item.added with item.type == "function_call")
                if et == "response.output_item.added":
                    item = getattr(event, "item", None)
                    if not item:
                        continue
                    if getattr(item, "type", None) == "function_call":
                        call_id = getattr(item, "id", None) or getattr(item, "call_id", None)
                        name = getattr(item, "name", None)
                        arguments = getattr(item, "arguments", None)  # may be complete already
                        if call_id and name:
                            pending_calls[call_id] = {"name": name, "arguments": arguments or ""}
                    continue

                # Some SDKs stream function args incrementally
                if et == "response.function_call_arguments.delta":
                    call_id = getattr(event, "call_id", None)
                    delta = getattr(event, "delta", "") or ""
                    if call_id and call_id in pending_calls:
                        pending_calls[call_id]["arguments"] = (pending_calls[call_id].get("arguments") or "") + delta
                    continue

                # Tool call is ready
                if et == "response.function_call.completed":
                    call_id = getattr(event, "call_id", None)
                    if not call_id or call_id not in pending_calls:
                        continue

                    call = pending_calls.pop(call_id)
                    tool_name = call.get("name")
                    raw_args = call.get("arguments") or "{}"

                    fn = TOOL_IMPL.get(tool_name)
                    if not fn:
                        # If model asked for an unknown tool, we fail safely.
                        yield _sse("error", {"message": f"Unknown tool requested: {tool_name}"})
                        yield _sse("done", {"ok": False})
                        return

                    try:
                        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                    except Exception:
                        args = {}

                    # Call local tool
                    try:
                        tool_out = fn(**args)
                    except TypeError:
                        tool_out = {"ok": False, "error_code": "BAD_TOOL_ARGS"}
                    except Exception as e:
                        logger.exception("tool_exec_error tool=%s", tool_name)
                        tool_out = {"ok": False, "error_code": "TOOL_EXEC_ERROR", "message": str(e)}

                    # Send tool output back into the SAME stream (SDK supports this via stream.send_* in some versions)
                    # Not all SDK versions expose the same helper; so we try both common patterns.
                    sent = False
                    for method_name in ("send_tool_output", "send_function_call_output"):
                        method = getattr(stream, method_name, None)
                        if callable(method):
                            method(call_id=call_id, output=tool_out)
                            sent = True
                            break

                    if not sent:
                        # If your SDK doesn't support in-stream tool outputs, you MUST do a 2nd call.
                        yield _sse(
                            "error",
                            {
                                "message": (
                                    "Your OpenAI SDK stream object doesn't support sending tool outputs back in-stream "
                                    "(no send_tool_output/send_function_call_output). "
                                    "Update the openai package or switch to a 2-call loop."
                                )
                            },
                        )
                        yield _sse("done", {"ok": False})
                        return

            yield _sse("done", {"ok": True})

    except Exception as e:
        logger.exception("stream_chat error")
        yield _sse("error", {"message": str(e)})
        yield _sse("done", {"ok": False})