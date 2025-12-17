import os
import json
import logging
from typing import List, Dict, Any

from openai import OpenAI

from app.schemas import ChatRequest
from app import tools as local_tools
from app.tool_schemas import TOOLS

logger = logging.getLogger("app.agent")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

TOOL_IMPL = {
    "get_medication": local_tools.get_medication,
    "get_user_prescriptions": local_tools.get_user_prescriptions,
    "check_user_prescription": local_tools.check_user_prescription,
}


def _conversation_to_messages(conversation: List[dict]) -> List[dict]:
    msgs = []
    for m in conversation or []:
        role = m.get("role")
        content = str(m.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            msgs.append(
                {
                    "role": role,
                    "content": [
                        {
                            "type": "input_text" if role == "user" else "output_text",
                            "text": content,
                        }
                    ],
                }
            )
    return msgs


def _to_dict(item: Any) -> dict:
    # SDK output items are Pydantic models; convert safely to plain dict
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if isinstance(item, dict):
        return item
    return {"type": getattr(item, "type", "unknown")}


def handle_chat(payload: ChatRequest) -> dict:
    messages: List[Dict[str, Any]] = _conversation_to_messages(payload.conversation)

    system_prompt = (
        "You are PharmAI, a pharmacy assistant.\n"
        "Rules:\n"
        "- Use tools whenever factual DB info is required.\n"
        "- Never invent medication, stock, or prescription data.\n"
        "- Ask for clarification only if required inputs are missing.\n"
        "- If the user asks for medical advice, recommend consulting a clinician.\n"
        "- Be concise and clear.\n"
    )

    for _ in range(8):  # small guard against infinite tool loops
        resp = client.responses.create(
            model=MODEL,
            instructions=system_prompt,
            input=messages,
            tools=TOOLS,
            tool_choice="auto",
            store=False,
        )

        output_items = resp.output or []

        tool_calls = [it for it in output_items if getattr(it, "type", None) == "function_call"]

        # No tool calls => return the assistant text
        if not tool_calls:
            return {"assistant": resp.output_text or ""}

        # Execute tool calls and append results exactly like the docs
        for call in tool_calls:
            name = getattr(call, "name", None)
            call_id = getattr(call, "call_id", None)
            raw_args = getattr(call, "arguments", None) or "{}"

            if not name or not call_id:
                raise RuntimeError("Malformed tool call from model (missing name/call_id).")

            fn = TOOL_IMPL.get(name)
            if not fn:
                raise RuntimeError(f"Unknown tool requested: {name}")

            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except Exception:
                args = {}

            try:
                result = fn(**args)
            except Exception as e:
                logger.exception("Tool execution failed: %s", name)
                result = {"ok": False, "error": str(e)}

            # Append the tool call itself (as dict)
            messages.append(_to_dict(call))

            # Append the tool output (output MUST be a string to avoid input[x].output type errors)
            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )

    return {"assistant": "I ran into a loop while trying to complete that. Can you rephrase your request?"}