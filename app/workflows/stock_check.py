# app/workflows/stock_check.py
# Workflow: Stock check (is a medication available / can it be picked up today?)
import logging

from app.tools import get_medication_stock

logger = logging.getLogger("app.workflows.stock_check")


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    """Handle STOCK_CHECK intent: resolve medication from intent and return stock availability."""
    query = (getattr(intent, "medication_query", None) or last_user or "").strip()
    logger.info("STOCK_CHECK query=%r last_user=%r user_id=%r", query, last_user, user_id)

    if not query:
        return {
            "assistant": "Which medication should I check stock for? (e.g., 'Advil')",
            "intent": intent.model_dump(),
        }

    res = get_medication_stock(query)
    if not res.get("found"):
        return {
            "assistant": res.get("message", "I couldn't find that medication in the demo database."),
            "intent": intent.model_dump(),
            "tool": res,
        }

    med = res.get("med") or {}
    display = f"{med.get('brand_name')} ({med.get('generic_name')}) {med.get('strength')}".strip()

    if res.get("in_stock"):
        # If they asked “today”, answer that directly (still fine if they didn’t).
        if "today" in (last_user or "").lower() or res.get("can_pickup_today"):
            return {
                "assistant": f"Yes — **{display}** is in stock, so you can pick it up today.",
                "intent": intent.model_dump(),
                "tool": res,
            }
        return {
            "assistant": f"Yes — **{display}** is in stock.",
            "intent": intent.model_dump(),
            "tool": res,
        }

    return {
        "assistant": f"No — **{display}** is currently out of stock.",
        "intent": intent.model_dump(),
        "tool": res,
    }