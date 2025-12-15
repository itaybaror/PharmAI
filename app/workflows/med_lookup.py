# app/workflows/med_lookup.py
# Workflow 1: Medication Information & Safe Usage (label-style facts; no personalized advice)
import logging

from app.tools import get_medication_by_name, resolve_medication_from_text

logger = logging.getLogger("app.workflows.med_lookup")


def infer_medication_from_history(conversation: list[dict]) -> str | None:
    """Find the most recently mentioned medication in the conversation (newest message first)."""
    # Walk backwards so we grab the most recent medication reference
    for m in reversed(conversation):
        text = str(m.get("content") or "")
        med = resolve_medication_from_text(text)
        if med:
            return med
    return None


def build_med_info_response(med: dict) -> str:
    """Format a medication record into a label-style response string."""
    parts: list[str] = []

    # Title/header line
    if med.get("name"):
        parts.append(f"**{med['name']}**")

    # Only include fields that exist (keeps output clean)
    if med.get("active_ingredients"):
        parts.append("Active ingredient(s): " + ", ".join(med["active_ingredients"]))

    if med.get("dosage_instructions"):
        parts.append("Usage instructions (label-style): " + str(med["dosage_instructions"]))

    if med.get("warnings"):
        parts.append("Warnings: " + str(med["warnings"]))

    # Always include a disclaimer line for safety / scope
    parts.append("For personal medical advice, consult a healthcare professional.")
    return "\n\n".join(parts)


def handle(intent, last_user: str, conversation: list[dict]) -> dict:
    """Workflow handler for MED_LOOKUP: resolve medication, fetch facts via tool, and build response."""
    logger.info("MED_LOOKUP last_user=%r", last_user)

    # Prefer the structured extraction from intent; fall back to raw user text
    query = (getattr(intent, "medication_query", None) or last_user or "").strip()

    # Multi-turn support: if the user asks "what are the warnings?" reuse the last medication mentioned
    inferred = infer_medication_from_history(conversation)

    # Gate only if confidence is low AND we have no medication signal to work with
    if getattr(intent, "confidence", 0.0) < 0.7 and not (resolve_medication_from_text(query) or inferred):
        logger.info("MED_LOOKUP low confidence=%.2f no med resolved", getattr(intent, "confidence", 0.0))
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

    # If the current message doesn't name a medication, substitute the inferred one from history
    if not resolve_medication_from_text(query) and inferred:
        logger.info("MED_LOOKUP using inferred medication=%r", inferred)
        query = inferred

    # Tool call: resolves the medication and returns label-style fields
    tool_result = get_medication_by_name(query)

    if not tool_result.get("found"):
        return {
            "assistant": tool_result.get("message", "I couldn't find that medication."),
            "intent": intent.model_dump(),
            "tool": tool_result,
        }

    med = tool_result["med"]

    # If Rx is required, keep response factual and avoid personalized guidance
    if med.get("requires_prescription"):
        return {
            "assistant": (
                f"**{med['name']}** requires a prescription. "
                "I can share label-style facts, but for whether it’s appropriate for you, please consult a licensed clinician."
            ),
            "intent": intent.model_dump(),
            "tool": tool_result,
        }

    return {
        "assistant": build_med_info_response(med),
        "intent": intent.model_dump(),
        "tool": tool_result,
    }