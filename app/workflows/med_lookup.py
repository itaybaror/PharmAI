# app/workflows/med_lookup.py
import logging

from app.tools import get_medication_by_name, resolve_medication_from_text

logger = logging.getLogger("app.workflows.med_lookup")


def infer_medication_from_history(conversation: list[dict]) -> str | None:
    for m in reversed(conversation):
        text = str(m.get("content") or "")
        med = resolve_medication_from_text(text)
        if med:
            return med
    return None


def build_med_info_response(med: dict) -> str:
    parts: list[str] = []

    if med.get("name"):
        parts.append(f"**{med['name']}**")

    if med.get("active_ingredients"):
        parts.append("Active ingredient(s): " + ", ".join(med["active_ingredients"]))

    if med.get("dosage_instructions"):
        parts.append("Usage instructions (label-style): " + str(med["dosage_instructions"]))

    if med.get("warnings"):
        parts.append("Warnings: " + str(med["warnings"]))

    parts.append("For personal medical advice, consult a healthcare professional.")
    return "\n\n".join(parts)


def handle(intent, last_user: str, conversation: list[dict]) -> dict:
    logger.info("MED_LOOKUP last_user=%r", last_user)

    query = (getattr(intent, "medication_query", None) or last_user or "").strip()
    inferred = infer_medication_from_history(conversation)

    # Gate only if we truly have no medication signal at all.
    if getattr(intent, "confidence", 0.0) < 0.7 and not (resolve_medication_from_text(query) or inferred):
        logger.info("MED_LOOKUP low confidence=%.2f no med resolved", getattr(intent, "confidence", 0.0))
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

    if not resolve_medication_from_text(query) and inferred:
        logger.info("MED_LOOKUP using inferred medication=%r", inferred)
        query = inferred

    tool_result = get_medication_by_name(query)

    if not tool_result.get("found"):
        return {
            "assistant": tool_result.get("message", "I couldn't find that medication."),
            "intent": intent.model_dump(),
            "tool": tool_result,
        }

    med = tool_result["med"]

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