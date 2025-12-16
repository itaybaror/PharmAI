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
    intent: Literal[
        "MED_LOOKUP",
        "USER_PRESCRIPTIONS",
        "STOCK_CHECK",
        "PRESCRIPTION_CHECK",
        "UNKNOWN",
    ]

    medication_query: str | None = Field(default=None)

    # MED_LOOKUP: what part of the medication info is being requested?
    med_info_type: Literal["FULL", "WARNINGS", "DOSAGE", "INGREDIENTS"] = "FULL"

    # MED_LOOKUP: flag personalized medical advice / diagnosis / suitability
    needs_clinician: bool = False
    clinician_reason: str | None = Field(default=None)

    # USER_PRESCRIPTIONS: what is the user trying to do?
    prescriptions_action: Literal["LIST", "HAS", "UNKNOWN"] = "UNKNOWN"

    confidence: float = Field(ge=0, le=1)


def detect_intent(user_text: str) -> IntentDetection:
    today = datetime.now().strftime("%A, %B %d, %Y")
    user_text = (user_text or "").strip()

    resp = client.responses.parse(
        model=MODEL,
        store=False,
        instructions=(
            f"Today is {today}. Return a JSON object matching the provided schema.\n\n"
            "Classify the user's message into exactly one intent:\n"
            "- USER_PRESCRIPTIONS: asks about THEIR prescriptions (list them, or ask if they have one for a drug)\n"
            "- STOCK_CHECK: asks if we have it / in stock / available\n"
            "- PRESCRIPTION_CHECK: asks if Rx/prescription is required for a medication\n"
            "- MED_LOOKUP: asks for factual label-style info (ingredients, warnings, standard directions)\n"
            "- UNKNOWN: anything else\n\n"
            "Extract medication_query if a medication is mentioned (include strength like '200mg' if present).\n\n"
            "If intent is USER_PRESCRIPTIONS, set prescriptions_action:\n"
            "- LIST: e.g., 'what are my prescriptions', 'list my meds'\n"
            "- HAS: e.g., 'do i have a prescription for zoloft', 'am i prescribed augmentin'\n"
            "- UNKNOWN: otherwise\n\n"
            "If intent is MED_LOOKUP, set med_info_type:\n"
            "- INGREDIENTS: asks what's in it / active ingredients\n"
            "- WARNINGS: asks warnings / side effects / risks\n"
            "- DOSAGE: asks label-style directions / how to take\n"
            "- FULL: otherwise\n\n"
            "Set needs_clinician=True if the user asks for personalized medical advice, diagnosis, "
            "whether it's appropriate for them, drug interactions based on their situation, pregnancy/breastfeeding safety, "
            "or anything that depends on personal medical context.\n"
            "If needs_clinician=True, set clinician_reason to ONE short user-facing sentence addressed to the user.\n"
            "Set confidence from 0 to 1."
        ),
        input=user_text,
        text_format=IntentDetection,
    )

    out = resp.output_parsed
    logger.info(
        "intent=%s confidence=%.2f med_query=%r med_info_type=%s needs_clinician=%s prescriptions_action=%s",
        out.intent,
        out.confidence,
        out.medication_query,
        out.med_info_type,
        out.needs_clinician,
        out.prescriptions_action,
    )
    return out