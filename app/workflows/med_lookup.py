# app/workflows/med_lookup.py
# Workflow 1: Medication Information & Safe Usage
# Goal: return label-style facts (ingredients / warnings / directions). Avoid personalized medical advice.
import logging

from app.tools import get_medication_by_name

logger = logging.getLogger("app.workflows.med_lookup")


def build_med_response(med: dict, section: str) -> str:
    """Build a response for FULL/WARNINGS/DOSAGE/INGREDIENTS using label-style facts."""
    name = med.get("name") or "Medication"
    disclaimer = "For personal medical advice, consult a healthcare professional."

    if section == "WARNINGS":
        warnings = med.get("warnings") or "Not available."
        return f"**{name}**\n\nWarnings: {warnings}\n\n{disclaimer}"

    if section == "DOSAGE":
        dosage = med.get("dosage_instructions") or "Not available."
        return f"**{name}**\n\nUsage instructions (label-style): {dosage}\n\n{disclaimer}"

    if section == "INGREDIENTS":
        ingredients = ", ".join(med.get("active_ingredients") or []) or "Not available."
        return f"**{name}**\n\nActive ingredient(s): {ingredients}\n\n{disclaimer}"

    # FULL card
    parts: list[str] = [f"**{name}**"]

    ingredients = ", ".join(med.get("active_ingredients") or [])
    if ingredients:
        parts.append("Active ingredient(s): " + ingredients)

    if med.get("dosage_instructions"):
        parts.append("Usage instructions (label-style): " + str(med["dosage_instructions"]))

    if med.get("warnings"):
        parts.append("Warnings: " + str(med["warnings"]))

    parts.append(disclaimer)
    return "\n\n".join(parts)


def _tool_error(intent, res: dict) -> dict:
    """Convert a tools.py error_code into a user-facing reply (and log it once)."""
    code = res.get("error_code") or "TOOL_ERROR"
    logger.warning("MED_LOOKUP tool_error code=%s", code)

    if code in {"MISSING_MEDICATION_QUERY", "MED_NOT_FOUND"}:
        msg = "I couldn't find that medication in the demo database. Try a brand or generic name (e.g., 'Advil', 'Ibuprofen')."
    else:
        msg = "Something went wrong while looking that up."

    return {"assistant": msg, "intent": intent.model_dump(), "tool": res}


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    """Resolve medication, fetch facts via tool, and respond with the requested info section."""
    logger.info("MED_LOOKUP last_user=%r", last_user)

    # Intent should resolve medication_query using conversation context.
    query = (getattr(intent, "medication_query", None) or "").strip()
    if not query:
        # This is conversational clarification, not a tools error.
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

    tool_result = get_medication_by_name(query)
    if not tool_result.get("ok"):
        return _tool_error(intent, tool_result)

    med = tool_result["med"]
    section = getattr(intent, "med_info_type", "FULL")
    logger.info("MED_LOOKUP medication_query=%r section=%s", query, section)

    # If Rx is required, we still share label-style facts, but add a clear Rx note.
    prefix = "Prescription-only medication.\n\n" if med.get("requires_prescription") else ""

    return {
        "assistant": prefix + build_med_response(med, section),
        "intent": intent.model_dump(),
        "tool": tool_result,
    }