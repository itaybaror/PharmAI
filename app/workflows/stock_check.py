# app/workflows/stock_check.py
# Workflow: Stock check (is a medication available / can it be picked up today?)
import logging

from app.tools import get_medication_stock

logger = logging.getLogger("app.workflows.stock_check")


def _display_from_med(m: dict) -> str:
    """Format a med summary dict (from tools) for chat output."""
    return f"{m.get('brand_name')} ({m.get('generic_name')}) {m.get('strength')}".strip()


def _tool_error(intent, res: dict) -> dict:
    """Convert a tools.py error_code into a user-facing reply (and log it once)."""
    code = res.get("error_code") or "TOOL_ERROR"
    logger.warning("STOCK_CHECK tool_error code=%s", code)

    if code in {"MISSING_MEDICATION_QUERY", "MED_NOT_FOUND"}:
        msg = "I couldn't find that medication in the demo database. Try a brand or generic name (e.g., 'Augmentin', 'Amoxicillin')."
    else:
        msg = "Something went wrong while checking stock."

    return {"assistant": msg, "intent": intent.model_dump(), "tool": res}


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    """Handle STOCK_CHECK intent: resolve medication from intent and return stock availability."""
    # Intent should resolve medication_query using conversation context.
    query = (getattr(intent, "medication_query", None) or "").strip()
    logger.info("STOCK_CHECK medication_query=%r last_user=%r user_id=%r", query, last_user, user_id)

    if not query:
        # Conversational clarification, not a tools error.
        return {
            "assistant": "Which medication should I check stock for? (e.g., 'Advil')",
            "intent": intent.model_dump(),
        }

    res = get_medication_stock(query)
    if not res.get("ok"):
        return _tool_error(intent, res)

    med = res.get("med") or {}
    display = _display_from_med(med)

    # If they asked “today”, answer in that framing (demo assumption: in-stock => pickup today).
    wants_today = "today" in (last_user or "").lower()

    if med.get("in_stock", True):
        msg = f"Yes — **{display}** is in stock."
        if wants_today:
            msg = f"Yes — **{display}** is in stock, so you can pick it up today."
        return {"assistant": msg, "intent": intent.model_dump(), "tool": res}

    msg = f"No — **{display}** is currently out of stock."
    if wants_today:
        msg = f"No — **{display}** is out of stock today."
    return {"assistant": msg, "intent": intent.model_dump(), "tool": res}