# app/agent.py
import logging

from app.intent import detect_intent
from app.schemas import ChatRequest
from app.tools import get_medication_by_name, resolve_medication_from_text

logger = logging.getLogger("app.agent")


def get_last_user_message(conversation: list[dict]) -> str:
    for m in reversed(conversation):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


def infer_medication_from_history(conversation: list[dict]) -> str | None:
    # Look through both user + assistant messages (newest first)
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


def handle_med_lookup(intent, last_user: str, conversation: list[dict]) -> dict:
    logger.info("MED_LOOKUP last_user=%r", last_user)

    if getattr(intent, "confidence", 0.0) < 0.7:
        logger.info("MED_LOOKUP low confidence=%.2f", getattr(intent, "confidence", 0.0))
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

    query = (getattr(intent, "medication_query", None) or last_user or "").strip()
    logger.info("MED_LOOKUP initial query=%r", query)

    if not resolve_medication_from_text(query):
        prior = infer_medication_from_history(conversation)
        logger.info("MED_LOOKUP inferred from history=%r", prior)
        if prior:
            query = prior
        else:
            return {
                "assistant": "Which medication are you asking about? (brand or generic name is fine)",
                "intent": intent.model_dump(),
            }

    tool_result = get_medication_by_name(query)

    if not tool_result.get("found"):
        logger.info("MED_LOOKUP tool not found query=%r", query)
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


def handle_stock_check(intent, last_user: str, conversation: list[dict]) -> dict:
    return {
        "assistant": "STOCK_CHECK workflow not implemented yet.",
        "intent": intent.model_dump(),
    }


def handle_prescription_check(intent, last_user: str, conversation: list[dict]) -> dict:
    return {
        "assistant": "PRESCRIPTION_CHECK workflow not implemented yet.",
        "intent": intent.model_dump(),
    }


ROUTES = {
    "MED_LOOKUP": handle_med_lookup,
    "STOCK_CHECK": handle_stock_check,
    "PRESCRIPTION_CHECK": handle_prescription_check,
}


def handle_chat(payload: ChatRequest) -> dict:
    last_user = get_last_user_message(payload.conversation)
    logger.info("handle_chat conversation_len=%s last_user=%r", len(payload.conversation), last_user)

    intent = detect_intent(last_user)
    logger.info(
        "intent=%s confidence=%.2f med_query=%r",
        getattr(intent, "intent", None),
        getattr(intent, "confidence", 0.0),
        getattr(intent, "medication_query", None),
    )

    handler = ROUTES.get(getattr(intent, "intent", ""))
    if handler:
        return handler(intent, last_user, payload.conversation)

    return {
        "assistant": f"Detected intent: {intent.intent} (workflow not implemented yet)",
        "intent": intent.model_dump(),
    }