from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field
from openai import OpenAI
import os

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


class IntentDetection(BaseModel):
    intent: Literal["MED_LOOKUP", "STOCK_CHECK", "PRESCRIPTION_CHECK", "UNKNOWN"]
    medication_query: Optional[str] = Field(default=None)
    confidence: float = Field(ge=0, le=1)


def detect_intent(user_text: str) -> IntentDetection:
    today = datetime.now().strftime("%A, %B %d, %Y")

    resp = client.responses.parse(
        model=MODEL,
        store=False,
        instructions=(
            f"Today is {today}. Classify the user's message into one intent:\n"
            "- STOCK_CHECK: asks if we have it / in stock / available\n"
            "- PRESCRIPTION_CHECK: asks if Rx/prescription is required\n"
            "- MED_LOOKUP: asks for facts like usage instructions/ingredient/warnings\n"
            "- UNKNOWN: anything else\n"
            "Extract medication_query (include strength like '200mg' if present)."
        ),
        input=user_text,
        text_format=IntentDetection,
    )

    return resp.output_parsed