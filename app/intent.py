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
    intent: Literal["MED_LOOKUP", "STOCK_CHECK", "PRESCRIPTION_CHECK", "UNKNOWN"]
    medication_query: str | None = Field(default=None)

    # For MED_LOOKUP: what part of the medication info is being requested?
    med_info_type: Literal["FULL", "WARNINGS", "DOSAGE", "INGREDIENTS"] = "FULL"

    # If the message asks for personalized medical advice/diagnosis/suitability, flag it.
    needs_clinician: bool = False
    clinician_reason: str | None = Field(default=None)

    confidence: float = Field(ge=0, le=1)


def detect_intent(user_text: str) -> IntentDetection:
    today = datetime.now().strftime("%A, %B %d, %Y")
    user_text = (user_text or "").strip()

    resp = client.responses.parse(
        model=MODEL,
        store=False,
        instructions=(
            f"Today is {today}. Return a JSON object matching the provided schema.\n\n"
            "Pick exactly one intent:\n"
            "- STOCK_CHECK: asks if we have it / in stock / available\n"
            "- PRESCRIPTION_CHECK: asks if Rx/prescription is required\n"
            "- MED_LOOKUP: asks for factual label-style info (ingredients, warnings, standard directions)\n"
            "- UNKNOWN: anything else\n\n"
            "Extract medication_query only if the user explicitly names a medication "
            "(include strength like '200mg' if present). Otherwise set it to null.\n\n"
            "If intent is MED_LOOKUP, choose med_info_type using these STRICT rules:\n"
            "- WARNINGS only if the user explicitly asks for warnings/side effects/risks/contraindications.\n"
            "- DOSAGE only if the user explicitly asks for directions/how to take/dosage/when to take.\n"
            "- INGREDIENTS only if the user explicitly asks for ingredients/what's in it/active ingredient.\n"
            "- FULL for general requests like 'tell me about it', 'share the label-style facts', "
            "'tell me all the information', or if unclear.\n\n"
            "Examples:\n"
            "User: 'what are the warnings for zoloft?' -> intent=MED_LOOKUP, med_info_type=WARNINGS\n"
            "User: 'share the label-style facts for zoloft' -> intent=MED_LOOKUP, med_info_type=FULL\n"
            "User: 'tell me about ibuprofen' -> intent=MED_LOOKUP, med_info_type=FULL\n"
            "User: 'what are the active ingredients in advil?' -> intent=MED_LOOKUP, med_info_type=INGREDIENTS\n\n"
            "Set needs_clinician=True if the user asks for personalized medical advice/diagnosis/suitability "
            "(e.g., 'should I take this', age/pregnancy/breastfeeding, interactions for their situation).\n"
            "If needs_clinician=True, clinician_reason must be ONE short user-facing sentence.\n"
            "If needs_clinician=False, clinician_reason must be null.\n\n"
            "Set confidence from 0 to 1."
        ),
        input=user_text,
        text_format=IntentDetection,
    )

    out = resp.output_parsed
    logger.info(
        "intent=%s confidence=%.2f med_query=%r med_info_type=%s needs_clinician=%s",
        out.intent,
        out.confidence,
        out.medication_query,
        out.med_info_type,
        out.needs_clinician,
    )
    return out