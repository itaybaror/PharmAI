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


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    """Resolve medication, fetch facts via tool, and respond with the requested info section."""
    logger.info("MED_LOOKUP last_user=%r", last_user)

    # Intent should resolve medication_query using conversation context.
    query = (getattr(intent, "medication_query", None) or "").strip()
    if not query:
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

    logger.info("MED_LOOKUP medication_query=%r", query)
    tool_result = get_medication_by_name(query)

    if not tool_result.get("found"):
        return {
            "assistant": tool_result.get("message", "I couldn't find that medication."),
            "intent": intent.model_dump(),
            "tool": tool_result,
        }

    med = tool_result["med"]
    section = getattr(intent, "med_info_type", "FULL")
    logger.info("MED_LOOKUP section=%s", section)

    # If Rx is required, we still share label-style facts, but add a clear Rx note.
    prefix = ""
    if med.get("requires_prescription"):
        prefix = "Prescription-only medication.\n\n"

    return {
        "assistant": prefix + build_med_response(med, section),
        "intent": intent.model_dump(),
        "tool": tool_result,
    }