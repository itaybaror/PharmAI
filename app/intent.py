# app/intent.py
from datetime import datetime
from typing import Literal
import os
import logging

from pydantic import BaseModel, Field
from openai import OpenAI

logger = logging.getLogger("app.intent")

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


class IntentDetection(BaseModel):
    intent: Literal["MED_LOOKUP", "USER_PRESCRIPTIONS", "STOCK_CHECK", "UNKNOWN"]
    medication_query: str | None = Field(default=None)

    med_info_type: Literal["FULL", "WARNINGS", "DOSAGE", "INGREDIENTS", "PRESCRIPTION"] = "FULL"

    needs_clinician: bool = False
    clinician_reason: str | None = Field(default=None)

    prescriptions_action: Literal["LIST", "HAS", "UNKNOWN"] = "UNKNOWN"

    confidence: float = Field(ge=0, le=1)


def _format_recent_history(conversation: list[dict], max_messages: int = 10) -> str:
    recent = (conversation or [])[-max_messages:]
    lines: list[str] = []
    for m in recent:
        role = str(m.get("role") or "").strip().lower()
        content = str(m.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def detect_intent(conversation: list[dict]) -> IntentDetection:
    today = datetime.now().strftime("%A, %B %d, %Y")

    last_user = ""
    for m in reversed(conversation or []):
        if m.get("role") == "user":
            last_user = str(m.get("content") or "").strip()
            break

    history_text = _format_recent_history(conversation, max_messages=10)

    resp = client.responses.parse(
        model=MODEL,
        store=False,
        instructions=(
            f"Today is {today}. Return JSON matching the provided schema.\n\n"
            "You will be given recent conversation context.\n"
            "The LAST USER message is the one to act on.\n\n"
            "If the last user message is underspecified (e.g., 'how about Advil?', 'what about that?', 'is it in stock?'), "
            "use the conversation context to infer the intended workflow and resolve what the user is referring to.\n\n"
            "Choose exactly one intent:\n"
            "- USER_PRESCRIPTIONS: asks about THEIR prescriptions (list them, or check if they have one for a drug)\n"
            "- STOCK_CHECK: asks if we have it / in stock / available\n"
            "- MED_LOOKUP: asks for factual label-style info about a medication\n"
            "- UNKNOWN: anything else\n\n"
            "Extract medication_query if a medication is mentioned or implied.\n\n"
            "If intent is USER_PRESCRIPTIONS, set prescriptions_action:\n"
            "- LIST: e.g., 'what are my prescriptions', 'list my meds'\n"
            "- HAS: e.g., 'do I have a prescription for zoloft'\n"
            "- UNKNOWN: otherwise\n\n"
            "If intent is MED_LOOKUP, set med_info_type:\n"
            "- INGREDIENTS / WARNINGS / DOSAGE / PRESCRIPTION / FULL\n"
            "Use PRESCRIPTION for questions like: 'Do I need a prescription for it?', 'Is this prescription-only?', "
            "'Can I get this over the counter?'\n\n"
            "Set needs_clinician=True if the user asks for personalized medical advice, diagnosis, suitability, interactions based "
            "on personal context, pregnancy/breastfeeding safety, or anything that depends on personal medical context.\n"
            "If needs_clinician=True, set clinician_reason to ONE short user-facing sentence addressed to the user.\n"
            "Set confidence from 0 to 1."
        ),
        input=(
            "RECENT CONVERSATION:\n"
            f"{history_text}\n\n"
            "LAST USER MESSAGE:\n"
            f"{last_user}"
        ),
        text_format=IntentDetection,
    )

    out = resp.output_parsed
    logger.info(
        "intent=%s confidence=%.2f med_query=%r prescriptions_action=%s med_info_type=%s needs_clinician=%s",
        out.intent,
        out.confidence,
        out.medication_query,
        out.prescriptions_action,
        out.med_info_type,
        out.needs_clinician,
    )
    return out