# app/workflows/stock_check.py
# Workflow handler: Stock check (structured)
# Goal: Call tool(s) and return stock info. The responder will produce the final text.
import logging

from app.tools import get_medication_stock

logger = logging.getLogger("app.workflows.stock_check")


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    logger.info("STOCK_CHECK")

    query = (getattr(intent, "medication_query", None) or "").strip()
    if not query:
        return {"ok": False, "error_code": "MISSING_MEDICATION_QUERY", "type": "stock_check"}

    tool_result = get_medication_stock(query)
    if not tool_result.get("ok"):
        tool_result["type"] = "stock_check"
        return tool_result

    med = tool_result.get("med") or {}
    asked_today = "today" in (last_user or "").lower()

    return {
        "ok": True,
        "type": "stock_check",
        "asked_today": asked_today,
        "in_stock": bool(med.get("in_stock", True)),
        "med": med,
    }