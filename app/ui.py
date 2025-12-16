# app/ui.py
import json
import gradio as gr

from app.db import USERS
from app.schemas import ChatRequest
from app.agent import stream_chat


def mount_ui(app):
    user_choices = [(f"{u['full_name']} ({u['user_id']})", u["user_id"]) for u in USERS]
    default_user_id = USERS[0]["user_id"] if USERS else ""

    with gr.Blocks(fill_height=True) as demo:
        gr.Markdown("# PharmAI")

        user_id = gr.Dropdown(
            choices=user_choices,
            value=default_user_id,
            label="Demo user",
            interactive=True,
        )

        def _chat_fn(message: str, history: list[dict], user_id_value: str):
            # Gradio gives us the existing chat history; we forward it to the server so the agent stays stateless.
            conversation = list(history or [])
            conversation.append({"role": "user", "content": message})
            payload = ChatRequest(conversation=conversation, user_id=user_id_value)

            # stream_chat yields SSE-formatted chunks. We convert them into incremental assistant text for Gradio.
            assistant_text = ""
            sse_event = None

            for chunk in stream_chat(payload):
                # chunk is a string like: "event: delta\ndata: {...}\n\n"
                for line in (chunk or "").splitlines():
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("event:"):
                        sse_event = line.split(":", 1)[1].strip()
                        continue

                    if line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()

                        # Some events may send plain text; most should be JSON.
                        try:
                            data = json.loads(data_str) if data_str else {}
                        except Exception:
                            data = {"delta": data_str}

                        if sse_event == "delta":
                            delta = data.get("delta") or data.get("text") or ""
                            if delta:
                                assistant_text += delta
                                yield assistant_text
                        elif sse_event == "done":
                            # Final yield so UI ends on the completed message.
                            yield assistant_text
                            return
                        elif sse_event == "error":
                            msg = data.get("message") or data.get("error") or "Something went wrong."
                            assistant_text += f"\n\n{msg}"
                            yield assistant_text
                            return

            # Fallback: if the generator ended without a done event
            yield assistant_text

        gr.ChatInterface(
            fn=_chat_fn,  # generator => streaming in the UI
            additional_inputs=[user_id],
        )

    return gr.mount_gradio_app(app, demo, path="/ui")