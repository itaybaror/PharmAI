# app/workflows/stock_check.py
import logging

logger = logging.getLogger("app.workflows.stock_check")


def handle(intent, last_user: str, conversation: list[dict]) -> dict:
    logger.info("STOCK_CHECK last_user=%r", last_user)
    return {
        "assistant": "STOCK_CHECK workflow not implemented yet.",
        "intent": intent.model_dump(),
    }