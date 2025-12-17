# app/ui.py
import gradio as gr

from app.db import USERS
from app.agent import stream_chat

WELCOME = (
    "Hi! I’m PharmAI.\n\n"
    "Ask me about our medications, your prescriptions, or anything else related to your pharmacy needs. "
)

def mount_ui(app):
    user_choices = [(f"{u['full_name']} ({u['user_id']})", u["user_id"]) for u in USERS]
    default_user_id = USERS[0]["user_id"] if USERS else ""

    initial_history = [{"role": "assistant", "content": WELCOME}]

    with gr.Blocks(fill_height=True) as demo:
        gr.Markdown("# PharmAI")
        gr.Markdown("### To switch users, refresh the page and select a different demo user.")
        gr.Markdown("If english is not your preferred language, feel free to ask me questions in your native language! Although for now i may only recognize drug names and information in English.")

        user_id = gr.Dropdown(
            choices=user_choices,
            value=default_user_id,
            label="Demo user",
            interactive=True,
        )

        def _chat_fn(message: str, history: list[dict], user_id_value: str):
            conversation = [{"role": m.get("role"), "content": m.get("content")} for m in (history or [])]
            conversation.append({"role": "user", "content": message})
            # Stream the chat response
            # Stops when stream_chat returns
            # Continues as long as stream_chat yields text
            for text in stream_chat(conversation=conversation, user_id=user_id_value):
                yield text

        gr.ChatInterface(
            fn=_chat_fn,
            additional_inputs=[user_id],
            chatbot=gr.Chatbot(value=initial_history),
        )

    return gr.mount_gradio_app(app, demo, path="/ui")