# app/workflows/user_prescriptions.py
# Workflow: User prescriptions (list user's prescriptions; check if user has one for a drug)
import logging

from app.tools import get_user_prescriptions, user_has_prescription

logger = logging.getLogger("app.workflows.user_prescriptions")


def _display_med(m: dict) -> str:
    """Format a med summary dict (from tools) for chat output."""
    return f"{m.get('brand_name')} ({m.get('generic_name')}) {m.get('strength')}".strip()


def _tool_error(intent, res: dict) -> dict:
    """Convert a tool error response into a user-facing message (workflow owns the wording)."""
    code = res.get("error_code", "TOOL_ERROR")

    if code == "MISSING_USER_ID":
        msg = "Please select a demo user from the dropdown so I can check prescriptions."
    elif code == "USER_NOT_FOUND":
        msg = "That demo user doesn’t exist. Please select a user from the dropdown."
    elif code == "MISSING_MEDICATION_QUERY":
        msg = "Which medication should I check? (e.g., 'Zoloft')"
    elif code == "MED_NOT_FOUND":
        msg = "I couldn't find that medication in the demo database. Try a brand or generic name."
    else:
        msg = "Something went wrong while checking the demo database."

    logger.warning("USER_PRESCRIPTIONS tool_error=%s", code)

    return {
        "assistant": msg,
        "intent": intent.model_dump(),
        "tool_error": {"error_code": code},
    }


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    """Handle USER_PRESCRIPTIONS intent using the demo user_id passed from the UI."""
    action = getattr(intent, "prescriptions_action", "UNKNOWN")
    uid = (user_id or "").strip()

    logger.info("USER_PRESCRIPTIONS action=%s uid=%s", action, uid)

    if action == "LIST":
        res = get_user_prescriptions(uid)
        if not res.get("ok"):
            return _tool_error(intent, res)

        user = res.get("user") or {}
        meds = res.get("prescriptions") or []

        if not meds:
            return {
                "assistant": f"{user.get('full_name', 'This user')} has no prescriptions in the demo database.",
                "intent": intent.model_dump(),
                "tool": res,
            }

        lines = [f"Prescriptions for **{user.get('full_name', 'user')}**:"]
        for m in meds:
            lines.append(f"- {_display_med(m)}")

        return {"assistant": "\n".join(lines), "intent": intent.model_dump(), "tool": res}

    if action == "HAS":
        q = (getattr(intent, "medication_query", None) or "").strip()

        res = user_has_prescription(uid, q)
        if not res.get("ok"):
            return _tool_error(intent, res)

        med = res.get("med") or {}
        display = _display_med(med)

        if res.get("has_prescription"):
            return {
                "assistant": f"Yes — you have a prescription for **{display}**.",
                "intent": intent.model_dump(),
                "tool": res,
            }

        if not med.get("rx_required", False):
            return {
                "assistant": (
                    f"No — **{display}** is over-the-counter (no prescription required), "
                    "so it won’t appear in your prescriptions list."
                ),
                "intent": intent.model_dump(),
                "tool": res,
            }

        return {
            "assistant": f"No — you do not have a prescription for **{display}** in the demo database.",
            "intent": intent.model_dump(),
            "tool": res,
        }

    return {
        "assistant": "Do you want me to list your prescriptions, or check a specific medication?",
        "intent": intent.model_dump(),
    }