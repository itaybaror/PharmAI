# app/main.py
from __future__ import annotations

import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="PharmAI", version="0.0.1")


class ChatRequest(BaseModel):
    conversation: List[Dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat(payload: ChatRequest):
    last_user = next((m.get("content") for m in reversed(payload.conversation) if m.get("role") == "user"), "")
    return {
        "assistant": f"Echo: {last_user}",
        "debug": {"messages_received": len(payload.conversation)},
    }