# app/ui.py
import gradio as gr

from app.schemas import ChatRequest
from app.agent import handle_chat


def mount_ui(app):
    def _chat_fn(message: str, history: list[dict]):
        # history is already [{"role": "user"/"assistant", "content": "..."}] when type="messages"
        conversation = list(history)
        conversation.append({"role": "user", "content": message})

        result = handle_chat(ChatRequest(conversation=conversation))
        return result.get("assistant", "")

    demo = gr.ChatInterface(
        fn=_chat_fn,
        title="PharmAI Chat UI",
        description="Manual chat UI mounted into FastAPI at /ui",
    )

    return gr.mount_gradio_app(app, demo, path="/ui")