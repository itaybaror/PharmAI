# app/schemas.py
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # Client sends full history each time so the server can stay stateless.
    conversation: list[dict] = Field(default_factory=list)
    user_id: str | None = None