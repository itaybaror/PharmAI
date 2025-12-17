# app/main.py
import os
import logging

from fastapi import FastAPI

from app.agent import stream_chat
from app.ui import mount_ui

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s: %(name)s - %(message)s")

for name in (
    "gradio",
    "gradio.queueing",
    "gradio.routes",
    "gradio.networking",
    "httpx",
    "urllib3",
    "uvicorn.access",
):
    logging.getLogger(name).setLevel(logging.WARNING)

logger = logging.getLogger("app.main")
logger.info("Starting PharmAI (LOG_LEVEL=%s)", LOG_LEVEL)

app = FastAPI(title="PharmAI", version="0.0.1")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat_route(payload: dict):
    conversation = payload.get("conversation") or []
    user_id = payload.get("user_id")
    return stream_chat(conversation=conversation, user_id=user_id)


if os.getenv("ENABLE_UI", "1") == "1":
    print("PharmAI is running, UI: http://localhost:8080/ui")
    mount_ui(app)