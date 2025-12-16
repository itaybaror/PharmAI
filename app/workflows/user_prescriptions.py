# app/workflows/user_prescriptions.py
# Workflow handler: User prescriptions (structured)
# Goal: Call tool(s) and return structured results. The responder will produce the final text.
import logging

from app.tools import get_user_prescriptions, user_has_prescription

logger = logging.getLogger("app.workflows.user_prescriptions")


def handle(intent, last_user: str, conversation: list[dict], user_id: str | None) -> dict:
    logger.info("USER_PRESCRIPTIONS")

    uid = (user_id or "").strip()
    if not uid:
        return {"ok": False, "error_code": "MISSING_USER_ID", "type": "user_prescriptions"}

    action = getattr(intent, "prescriptions_action", "UNKNOWN")

    if action == "LIST":
        tool_result = get_user_prescriptions(uid)
        if not tool_result.get("ok"):
            tool_result["type"] = "user_prescriptions"
            tool_result["action"] = "LIST"
            return tool_result

        return {
            "ok": True,
            "type": "user_prescriptions",
            "action": "LIST",
            "user": tool_result.get("user"),
            "prescriptions": tool_result.get("prescriptions") or [],
        }

    if action == "HAS":
        q = (getattr(intent, "medication_query", None) or "").strip()
        if not q:
            return {"ok": False, "error_code": "MISSING_MEDICATION_QUERY", "type": "user_prescriptions", "action": "HAS"}

        tool_result = user_has_prescription(uid, q)
        if not tool_result.get("ok"):
            tool_result["type"] = "user_prescriptions"
            tool_result["action"] = "HAS"
            return tool_result

        return {
            "ok": True,
            "type": "user_prescriptions",
            "action": "HAS",
            "user": tool_result.get("user"),
            "has_prescription": bool(tool_result.get("has_prescription")),
            "med": tool_result.get("med"),
        }

    return {"ok": False, "error_code": "UNKNOWN_INTENT", "type": "user_prescriptions"}