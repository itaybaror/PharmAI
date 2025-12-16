# app/workflows/med_lookup.py
# Workflow handler: Medication lookup (structured)
# Goal: Call tool(s) and return structured facts. The responder will produce the final text.
import logging

from app.tools import get_medication_by_name

logger = logging.getLogger("app.workflows.med_lookup")


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    logger.info("MED_LOOKUP")

    query = (getattr(intent, "medication_query", None) or "").strip()
    if not query:
        # Let responder ask the clarification question
        return {"ok": False, "error_code": "MISSING_MEDICATION_QUERY", "type": "med_lookup"}

    tool_result = get_medication_by_name(query)
    if not tool_result.get("ok"):
        tool_result["type"] = "med_lookup"
        return tool_result

    section = getattr(intent, "med_info_type", "FULL")
    return {
        "ok": True,
        "type": "med_lookup",
        "section": section,  # FULL / WARNINGS / DOSAGE / INGREDIENTS / PRESCRIPTION
        "med": tool_result.get("med"),
    }