# app/workflows/user_prescriptions.py
# Workflow: User prescriptions (list user's prescriptions; check if user has one for a drug)
import logging

from app.tools import get_user_prescriptions, user_has_prescription

logger = logging.getLogger("app.workflows.user_prescriptions")


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    """Handle USER_PRESCRIPTIONS intent using the demo user_id passed from the UI."""
    uid = (user_id or "").strip()
    action = getattr(intent, "prescriptions_action", "UNKNOWN")

    logger.info("USER_PRESCRIPTIONS user_id=%r action=%s last_user=%r", uid, action, last_user)

    if not uid:
        return {
            "assistant": "Please select a demo user from the dropdown so I can check prescriptions.",
            "intent": intent.model_dump(),
        }

    if action == "LIST":
        res = get_user_prescriptions(uid)
        if not res.get("found_user"):
            return {
                "assistant": res.get("message", "Unknown demo user."),
                "intent": intent.model_dump(),
                "tool": res,
            }

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
            name = f"{m.get('brand_name')} ({m.get('generic_name')}) {m.get('strength')}".strip()
            lines.append(f"- {name}")
        return {"assistant": "\n".join(lines), "intent": intent.model_dump(), "tool": res}

    if action == "HAS":
        q = (getattr(intent, "medication_query", None) or "").strip()
        if not q:
            return {
                "assistant": "Which medication should I check? (e.g., 'Zoloft')",
                "intent": intent.model_dump(),
            }

        res = user_has_prescription(uid, q)
        if not res.get("found_user"):
            return {
                "assistant": res.get("message", "Unknown demo user."),
                "intent": intent.model_dump(),
                "tool": res,
            }
        if not res.get("found_med"):
            return {
                "assistant": res.get("message", "I couldn't find that medication."),
                "intent": intent.model_dump(),
                "tool": res,
            }

        med = res.get("med") or {}
        display = f"{med.get('brand_name')} ({med.get('generic_name')}) {med.get('strength')}".strip()

        if res.get("has_prescription"):
            return {
                "assistant": f"Yes — you have a prescription for **{display}**.",
                "intent": intent.model_dump(),
                "tool": res,
            }

        # If it's OTC, explain why it won't appear in the user's prescriptions list
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