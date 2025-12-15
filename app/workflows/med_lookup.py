# app/workflows/med_lookup.py
# Workflow 1: Medication Information & Safe Usage
# Goal: return label-style facts (ingredients / warnings / directions). Avoid personalized medical advice.
import logging

from app.tools import get_medication_by_name, resolve_medication_from_text

logger = logging.getLogger("app.workflows.med_lookup")


def infer_medication_from_history(conversation: list[dict]) -> str | None:
    """Find the most recently mentioned medication in the conversation (newest message first)."""
    for m in reversed(conversation):
        text = str(m.get("content") or "")
        med = resolve_medication_from_text(text)
        if med:
            return med
    return None


def build_med_response(med: dict, section: str) -> str:
    """Build a response for FULL/WARNINGS/DOSAGE/INGREDIENTS using label-style facts."""
    name = med.get("name") or "Medication"
    disclaimer = "For personal medical advice, consult a healthcare professional."

    # Return only the requested section when possible (feels more conversational)
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


def handle(intent, last_user: str, conversation: list[dict]) -> dict:
    """Resolve medication, fetch facts via tool, and respond with the requested info section."""
    logger.info("MED_LOOKUP last_user=%r", last_user)

    # Advice-seeking / suitability questions should be redirected
    if getattr(intent, "needs_clinician", False):
        reason = (getattr(intent, "clinician_reason", "") or "").strip()
        msg = reason if reason else "I can’t answer that safely without your medical context."
        if msg.lower().startswith(("asks for", "user asks", "the user asks")):
            msg = "I can’t answer that safely without your medical context."
        return {
            "assistant": msg + "\n\nFor personal medical advice, consult a healthcare professional.",
            "intent": intent.model_dump(),
        }

    # If the model extracted a medication name from THIS message, trust it and don't override with history.
    explicit = (getattr(intent, "medication_query", None) or "").strip()

    if explicit:
        query = explicit
        inferred = None
        logger.info("MED_LOOKUP using explicit medication_query=%r", query)
    else:
        query = (last_user or "").strip()
        inferred = infer_medication_from_history(conversation)
        logger.info("MED_LOOKUP initial query=%r inferred=%r", query, inferred)

        # Follow-up support: if user didn't name a med, reuse the last med mentioned
        if not resolve_medication_from_text(query) and inferred:
            query = inferred
            logger.info("MED_LOOKUP using inferred medication=%r", query)

    # If confidence is low and we still can't resolve any medication, ask for clarification
    if getattr(intent, "confidence", 0.0) < 0.7 and not (resolve_medication_from_text(query) or inferred):
        logger.info("MED_LOOKUP low confidence=%.2f no med resolved", getattr(intent, "confidence", 0.0))
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

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

    # If Rx is required, we still share label-style facts, but we add a clear Rx note.
    prefix = ""
    if med.get("requires_prescription"):
        prefix = "Prescription-only medication.\n\n"

    return {
        "assistant": prefix + build_med_response(med, section),
        "intent": intent.model_dump(),
        "tool": tool_result,
    }