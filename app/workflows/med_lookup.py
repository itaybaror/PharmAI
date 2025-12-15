# app/workflows/med_lookup.py
# Workflow 1: Medication Information & Safe Usage
# Goal: return label-style facts (ingredients / warnings / directions) and avoid personalized medical advice.
import logging

from app.tools import get_medication_by_name, resolve_medication_from_text

logger = logging.getLogger("app.workflows.med_lookup")


def infer_medication_from_history(conversation: list[dict]) -> str | None:
    """Find the most recently mentioned medication in the conversation (newest message first)."""
    # Walk backwards so the first match is the most recent medication mentioned
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

    # If the user asked for a specific section, return only that section (keeps responses conversational)
    if section == "WARNINGS":
        warnings = med.get("warnings") or "Not available."
        return f"**{name}**\n\nWarnings: {warnings}\n\n{disclaimer}"

    if section == "DOSAGE":
        dosage = med.get("dosage_instructions") or "Not available."
        return f"**{name}**\n\nUsage instructions (label-style): {dosage}\n\n{disclaimer}"

    if section == "INGREDIENTS":
        ingredients = ", ".join(med.get("active_ingredients") or []) or "Not available."
        return f"**{name}**\n\nActive ingredient(s): {ingredients}\n\n{disclaimer}"

    # FULL card: include all available label-style fields
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

    # If the LLM says the user is asking for personalized advice, stop early (handled as a safety gate)
    if getattr(intent, "needs_clinician", False):
        reason = (getattr(intent, "clinician_reason", "") or "").strip()

        # We want user-facing wording; if the model outputs meta text, replace it with a generic message
        msg = reason if reason else "I can’t answer that safely without your medical context."
        if msg.lower().startswith(("asks for", "user asks", "the user asks")):
            msg = "I can’t answer that safely without your medical context."

        return {
            "assistant": msg + "\n\nFor personal medical advice, consult a healthcare professional.",
            "intent": intent.model_dump(),
        }

    # If the model extracted a medication name from THIS message, trust it and do NOT override with history.
    # This prevents: user asks about Adderall -> we accidentally reuse the last drug (e.g., Advil).
    explicit = (getattr(intent, "medication_query", None) or "").strip()

    if explicit:
        query = explicit
        inferred = None
        logger.info("MED_LOOKUP using explicit medication_query=%r", query)
    else:
        # No explicit medication extracted, so we use the raw message and allow multi-turn inference.
        query = (last_user or "").strip()
        inferred = infer_medication_from_history(conversation)
        logger.info("MED_LOOKUP initial query=%r inferred=%r", query, inferred)

        # If the user asked a follow-up like "what are the warnings?" and didn't name a drug,
        # reuse the most recent medication mentioned earlier in the conversation.
        if not resolve_medication_from_text(query) and inferred:
            query = inferred
            logger.info("MED_LOOKUP using inferred medication=%r", query)

    # Gate: if confidence is low AND we still don't have a medication to look up, ask the user to clarify.
    if getattr(intent, "confidence", 0.0) < 0.7 and not (resolve_medication_from_text(query) or inferred):
        logger.info("MED_LOOKUP low confidence=%.2f no med resolved", getattr(intent, "confidence", 0.0))
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

    # Tool call: look up the medication from our synthetic DB
    tool_result = get_medication_by_name(query)

    if not tool_result.get("found"):
        # Important: if the user explicitly asked for a medication not in our DB (e.g., Adderall),
        # we should tell them it's not found rather than answering about a different drug.
        return {
            "assistant": tool_result.get("message", "I couldn't find that medication."),
            "intent": intent.model_dump(),
            "tool": tool_result,
        }

    med = tool_result["med"]

    # If Rx is required, stay factual and avoid giving guidance about whether they should take it.
    if med.get("requires_prescription"):
        return {
            "assistant": (
                f"**{med['name']}** requires a prescription. "
                "I can share label-style facts, but for whether it’s appropriate for you, please consult a licensed clinician."
            ),
            "intent": intent.model_dump(),
            "tool": tool_result,
        }

    # The LLM decided which section the user wants (warnings/dosage/ingredients/full).
    section = getattr(intent, "med_info_type", "FULL")
    logger.info("MED_LOOKUP section=%s", section)

    return {
        "assistant": build_med_response(med, section),
        "intent": intent.model_dump(),
        "tool": tool_result,
    }