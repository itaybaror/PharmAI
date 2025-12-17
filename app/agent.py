# app/agent.py
import os
import json
import logging
from typing import List, Dict, Any

from openai import OpenAI

from app.schemas import ChatRequest
from app import tools as local_tools
from app.tools import TOOLS
from app.db import USERS_BY_ID
from app.prompt import build_system_prompt

logger = logging.getLogger("app.agent")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def _conversation_to_messages(conversation: List[dict]) -> List[dict]:
    # IMPORTANT: everything you send in `input` is "input_*" (even prior assistant turns).
    msgs: List[Dict[str, Any]] = []
    for m in conversation or []:
        role = (m.get("role") or "").strip().lower()
        content = str(m.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            content_type = "input_text" if role == "user" else "output_text"
            msgs.append(
                {
                    "role": role,
                    "content": [{"type": content_type, "text": content}],
                }
            )
    return msgs


def _tool_call_to_input_item(call: Any) -> Dict[str, Any]:
    # Keep ONLY the fields the API expects for a tool call item.
    return {
        "type": "function_call",
        "call_id": getattr(call, "call_id", None),
        "name": getattr(call, "name", None),
        "arguments": getattr(call, "arguments", None) or "{}",
    }


def _call_local_tool(name: str, args: dict, user_id: str | None) -> dict:
    # user_id is selected by dropdown; do NOT rely on the model to provide it.
    if name == "get_medication":
        return local_tools.get_medication(args.get("query", ""))

    if name == "get_user_prescriptions":
        return local_tools.get_user_prescriptions(user_id or "")

    if name == "list_medications":
        rx_filter = args.get("rx_filter", "both")
        stock_filter = args.get("stock_filter", "both")
        return local_tools.list_medications(rx_filter=rx_filter, stock_filter=stock_filter)

    raise RuntimeError(f"Unknown tool requested: {name}")


def handle_chat(payload: ChatRequest) -> dict:
    messages: List[Dict[str, Any]] = _conversation_to_messages(payload.conversation)

    user = USERS_BY_ID.get((payload.user_id or "").strip()) if payload.user_id else None
    user_name = (user.get("full_name") if user else None) or "there"

    system_prompt = build_system_prompt(user_name)

    for _ in range(8):  # guard against infinite tool loops
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

        # No tool calls => return final assistant text
        if not tool_calls:
            return {"assistant": resp.output_text or ""}

        # Execute tool calls and append results like the docs
        for call in tool_calls:
            name = getattr(call, "name", None)
            call_id = getattr(call, "call_id", None)
            raw_args = getattr(call, "arguments", None) or "{}"

            if not name or not call_id:
                raise RuntimeError("Malformed tool call from model (missing name/call_id).")

            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except Exception:
                args = {}

            try:
                result = _call_local_tool(name, args, payload.user_id)
            except Exception as e:
                logger.exception("Tool execution failed: %s", name)
                result = {"ok": False, "error": str(e)}

            # Append the tool call item (so the call_id exists in the next request)
            call_item = _tool_call_to_input_item(call)
            if not call_item.get("call_id") or not call_item.get("name"):
                raise RuntimeError("Malformed tool call item after normalization.")
            messages.append(call_item)

            # Append the tool output (MUST be a string)
            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )

    return {"assistant": "I ran into a loop while trying to complete that. Can you rephrase your request?"}