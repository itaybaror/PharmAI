# app/ui.py
import gradio as gr

from app.db import USERS
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
            conversation = [{"role": m.get("role"), "content": m.get("content")} for m in (history or [])]
            conversation.append({"role": "user", "content": message})
            for text in stream_chat(conversation=conversation, user_id=user_id_value):
                yield text

        gr.ChatInterface(
            fn=_chat_fn,
            additional_inputs=[user_id],
        )

    return gr.mount_gradio_app(app, demo, path="/ui")