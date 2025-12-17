# app/main.py
import os
import logging

from fastapi import FastAPI

from app.schemas import ChatRequest
from app.agent import handle_chat
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
def chat_route(payload: ChatRequest):
    return handle_chat(payload)


if os.getenv("ENABLE_UI", "1") == "1":
    mount_ui(app)