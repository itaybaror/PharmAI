# app/agent.py
from app.intent import detect_intent
from app.tools import get_medication_by_name
from app.schemas import ChatRequest


def get_last_user_message(conversation: list[dict]) -> str:
    for m in reversed(conversation):
        if m.get("role") == "user":
            return str(m.get("content") or "")
    return ""


def build_med_info_response(med: dict) -> str:
    parts: list[str] = []

    parts.append(f"**{med['name']}**")

    if med.get("active_ingredients"):
        parts.append("Active ingredient(s): " + ", ".join(med["active_ingredients"]))

    if med.get("dosage_instructions"):
        parts.append("Usage instructions (label-style): " + med["dosage_instructions"])

    if med.get("warnings"):
        parts.append("Warnings: " + med["warnings"])

    parts.append("For personal medical advice, consult a healthcare professional.")
    return "\n\n".join(parts)


def handle_med_lookup(intent, last_user: str) -> dict:
    # Workflow 1: Medication Information & Safe Usage (no advice)
    if intent.confidence < 0.7:
        return {
            "assistant": "Which medication are you asking about? (e.g., 'Ibuprofen 200mg')",
            "intent": intent.model_dump(),
        }

    query = intent.medication_query or last_user
    tool_result = get_medication_by_name(query)

    if not tool_result["found"]:
        return {
            "assistant": tool_result["message"],
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


def handle_stock_check(intent, last_user: str) -> dict:
    # Workflow 2 (placeholder): Stock Check
    return {
        "assistant": "STOCK_CHECK workflow not implemented yet.",
        "intent": intent.model_dump(),
    }


def handle_prescription_check(intent, last_user: str) -> dict:
    # Workflow 3 (placeholder): Prescription Check
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
    intent = detect_intent(last_user)

    handler = ROUTES.get(intent.intent)
    # Go to appropriate workflow
    if handler:
        return handler(intent, last_user)

    return {
        "assistant": f"Detected intent: {intent.intent} (workflow not implemented yet)",
        "intent": intent.model_dump(),
    }