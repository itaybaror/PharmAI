# app/main.py
from fastapi import FastAPI

from app.schemas import ChatRequest
from app.agent import handle_chat

# FastAPI app entrypoint (this is what uvicorn loads)
app = FastAPI(title="PharmAI", version="0.0.1")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat_route(payload: ChatRequest):
    # main.py stays “thin”: validate request -> delegate to agent logic
    return handle_chat(payload)