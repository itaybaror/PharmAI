# app/agent.py
import os
import json
import logging
from typing import Any, Dict, Iterator, List

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
    UI stores conversation as:
      [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]

    Responses API expects:
      {"role":"user","content":[{"type":"input_text","text":"..."}]}
      {"role":"assistant","content":[{"type":"output_text","text":"..."}]}
    """
    msgs: List[Dict[str, Any]] = []
    for m in conversation or []:
        role = (m.get("role") or "").strip().lower()
        text = str(m.get("content") or "").strip()
        if role in {"user", "assistant"} and text:
            content_type = "input_text" if role == "user" else "output_text"
            msgs.append({"role": role, "content": [{"type": content_type, "text": text}]})
    return msgs


def _tool_call_to_input_item(call: Any) -> Dict[str, Any]:
    return {
        "type": "function_call",
        "call_id": getattr(call, "call_id", None),
        "name": getattr(call, "name", None),
        "arguments": getattr(call, "arguments", None) or "{}",
    }


def _call_local_tool(name: str, args: dict, user_id: str | None) -> dict:
    # user_id comes from the dropdown; do not rely on model-supplied user_id
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


def stream_chat(conversation: List[dict], user_id: str | None) -> Iterator[str]:
    """
    Proper streaming tool loop:
      - stream a response, yielding text deltas
      - after stream completes, if tool calls exist: execute tools, append tool outputs, repeat
    Yields the FULL assistant text so far each time (ideal for Gradio).
    """
    messages: List[Dict[str, Any]] = _conversation_to_messages(conversation)

    user = USERS_BY_ID.get((user_id or "").strip()) if user_id else None
    user_name = (user.get("full_name") if user else None) or "there"
    system_prompt = build_system_prompt(user_name)

    assistant_text = ""

    for _ in range(8):  # loop guard
        # 1) Stream model output
        with client.responses.stream(
            model=MODEL,
            instructions=system_prompt,
            input=messages,
            tools=TOOLS,
            tool_choice="auto",
            store=False,
        ) as stream:
            for event in stream:
                if getattr(event, "type", None) == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        assistant_text += delta
                        yield assistant_text

        final = stream.get_final_response()

        # 2) If model asked for tools, execute them and loop
        tool_calls = [it for it in (final.output or []) if getattr(it, "type", None) == "function_call"]
        if not tool_calls:
            return  # done (we already yielded the final text)

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
                result = _call_local_tool(name, args, user_id)
            except Exception as e:
                logger.exception("Tool execution failed: %s", name)
                result = {"ok": False, "error": str(e)}

            # Append tool call + output so the next request can continue correctly
            call_item = _tool_call_to_input_item(call)
            if not call_item.get("call_id") or not call_item.get("name"):
                raise RuntimeError("Malformed tool call item after normalization.")
            messages.append(call_item)

            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )

    yield assistant_text + "\n\nI ran into a loop while trying to complete that. Can you rephrase your request?"