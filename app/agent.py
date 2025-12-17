# app/agent.py
import os
import json
import logging
from typing import List, Dict, Any

from openai import OpenAI

from app import tools as local_tools
from app.tools import TOOLS
from app.db import USERS_BY_ID
from app.prompt import build_system_prompt

logger = logging.getLogger("app.agent")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def _conversation_to_messages(conversation: List[dict]) -> List[dict]:
    """
    Gradio ChatInterface history is stored in a simple format:
      [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]

    The Responses API expects messages shaped like:
      {"role":"user","content":[{"type":"input_text","text":"..."}]}
      {"role":"assistant","content":[{"type":"output_text","text":"..."}]}

    So we do a small conversion here (and keep only user/assistant text turns).
    """
    msgs: List[Dict[str, Any]] = []
    for m in conversation or []:
        role = (m.get("role") or "").strip().lower()
        content = str(m.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            content_type = "input_text" if role == "user" else "output_text"
            msgs.append({"role": role, "content": [{"type": content_type, "text": content}]})
    return msgs


def _tool_call_to_input_item(call: Any) -> Dict[str, Any]:
    """
    When we loop, we must include the original tool call item back in `input`
    so the API can match our later function_call_output by call_id.
    """
    return {
        "type": "function_call",
        "call_id": getattr(call, "call_id", None),
        "name": getattr(call, "name", None),
        "arguments": getattr(call, "arguments", None) or "{}",
    }


def _call_local_tool(name: str, args: dict, user_id: str | None) -> dict:
    """
    Execute the local Python tool implementation.
    Note: user_id comes from the UI dropdown and is injected server-side.
    The model should not be trusted to supply it.
    """
    if name == "get_medication":
        return local_tools.get_medication(args.get("query", ""))

    if name == "get_user_prescriptions":
        return local_tools.get_user_prescriptions(user_id or "")

    if name == "list_medications":
        return local_tools.list_medications(
            rx_filter=args.get("rx_filter", "both"),
            stock_filter=args.get("stock_filter", "both"),
        )

    raise RuntimeError(f"Unknown tool requested: {name}")


def handle_chat(conversation: List[dict], user_id: str | None) -> dict:
    """
    Non-streaming agent loop:
      - Call the model with tools enabled
      - If it requests tools, execute them and append tool call + tool output
      - Repeat until the model returns final text (or we hit a loop guard)
    """
    messages: List[Dict[str, Any]] = _conversation_to_messages(conversation)

    user = USERS_BY_ID.get((user_id or "").strip()) if user_id else None
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

        # iterate response.output, execute function calls, append outputs.
        tool_call_found = False
        for item in (resp.output or []):
            if getattr(item, "type", None) != "function_call":
                continue

            tool_call_found = True

            name = getattr(item, "name", None)
            call_id = getattr(item, "call_id", None)
            raw_args = getattr(item, "arguments", None) or "{}"

            if not name or not call_id:
                raise RuntimeError("Malformed tool call from model (missing name/call_id).")

            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except Exception:
                args = {}

            try:
                result = _call_local_tool(name, args, user_id)
            except Exception as e:
                logger.exception("Tool execution failed: %s", name)
                result = {"ok": False, "error": str(e)}

            # 1) Append the tool call itself so the next request can reference its call_id
            call_item = _tool_call_to_input_item(item)
            if not call_item.get("call_id") or not call_item.get("name"):
                raise RuntimeError("Malformed tool call item after normalization.")
            messages.append(call_item)

            # 2) Append the tool output (output must be a STRING)
            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )

        # If the model didn't request tools, we're done: return the assistant text.
        if not tool_call_found:
            return {"assistant": resp.output_text or ""}

    return {"assistant": "I ran into a loop while trying to complete that. Can you rephrase your request?"}