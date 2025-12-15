# app/workflows/prescription_check.py
import logging

logger = logging.getLogger("app.workflows.prescription_check")


def handle(intent, last_user: str, conversation: list[dict]) -> dict:
    logger.info("PRESCRIPTION_CHECK last_user=%r", last_user)
    return {
        "assistant": "PRESCRIPTION_CHECK workflow not implemented yet.",
        "intent": intent.model_dump(),
    }