# app/responder.py
import os
from openai import OpenAI
from typing import Iterator

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def stream_response(context: dict, language: str = "he") -> Iterator[str]:
    """
    Stream a natural-language response based on structured context.
    `context` comes from workflows (not raw user text).
    """

    system_prompt = (
        "You are a pharmacy assistant.\n"
        "Respond clearly and concisely.\n"
        "Use Hebrew if possible.\n"
        "Do not invent medical facts.\n"
        "If something is unknown, say so.\n"
    )

    user_prompt = f"""
Here is the structured result of the request:

{context}

Write a helpful response for the user.
"""

    with client.responses.stream(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta