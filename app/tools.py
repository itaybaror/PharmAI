# app/tools.py
import logging
from typing import Any

from app.db import MEDS, USERS_BY_ID, MEDS_BY_ID

logger = logging.getLogger("app.tools")


def _norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _find_medication_in_text(text: str) -> dict | None:
    t = _norm(text)
    if not t:
        return None

    for med in MEDS:
        brand = _norm(med.get("brand_name", ""))
        generic = _norm(med.get("generic_name", ""))

        if brand and brand in t:
            return med
        if generic and generic in t:
            return med

        for a in (med.get("aliases") or []):
            aa = _norm(a)
            if aa and aa in t:
                return med

    return None


def _get_user(user_id: str) -> tuple[dict | None, dict | None]:
    uid = (user_id or "").strip()
    if not uid:
        return None, {"ok": False, "error_code": "MISSING_USER_ID"}

    user = USERS_BY_ID.get(uid)
    if not user:
        return None, {"ok": False, "error_code": "USER_NOT_FOUND"}

    return user, None


def _get_medication(query: str) -> tuple[dict | None, dict | None]:
    q = (query or "").strip()
    if not q:
        return None, {"ok": False, "error_code": "MISSING_MEDICATION_QUERY"}

    med = _find_medication_in_text(q)
    if not med:
        return None, {"ok": False, "error_code": "MED_NOT_FOUND"}

    return med, None


def _med_summary(med: dict) -> dict:
    brand = med.get("brand_name") or ""
    generic = med.get("generic_name") or ""
    strength = med.get("strength") or ""
    display = f"{brand} ({generic}) {strength}".strip()

    return {
        "medication_id": med.get("medication_id"),
        "brand_name": med.get("brand_name"),
        "generic_name": med.get("generic_name"),
        "strength": med.get("strength"),
        "rx_required": bool(med.get("rx_required")),
        "in_stock": bool(med.get("in_stock", True)),
        "display_name": display,
    }


def get_medication(query: str) -> dict:
    logger.info("get_medication query=%r", query)

    med, err = _get_medication(query)
    if err:
        return err

    summary = _med_summary(med)
    return {
        "ok": True,
        "med": {
            "medication_id": summary["medication_id"],
            "name": summary["display_name"],
            "brand_name": summary["brand_name"],
            "generic_name": summary["generic_name"],
            "active_ingredients": med.get("active_ingredients", []),
            "form": med.get("form"),
            "strength": summary["strength"],
            "requires_prescription": summary["rx_required"],
            "in_stock": summary["in_stock"],
            "dosage_instructions": med.get("usage_instructions"),
            "warnings": med.get("warnings"),
        },
    }


def get_user_prescriptions(user_id: str) -> dict:
    logger.info("get_user_prescriptions user_id=%r", user_id)

    user, err = _get_user(user_id)
    if err:
        return err

    prescriptions: list[dict] = []
    for mid in (user.get("prescribed_medications") or []):
        m = MEDS_BY_ID.get(mid)
        if m:
            prescriptions.append(_med_summary(m))

    return {
        "ok": True,
        "user": {"user_id": user.get("user_id"), "full_name": user.get("full_name")},
        "prescriptions": prescriptions,
    }


def check_user_prescription(user_id: str, medication_query: str) -> dict:
    logger.info("check_user_prescription user_id=%r medication_query=%r", user_id, medication_query)

    user, err = _get_user(user_id)
    if err:
        return err

    med, err = _get_medication(medication_query)
    if err:
        return err

    prescribed = set(user.get("prescribed_medications") or [])
    summary = _med_summary(med)

    return {
        "ok": True,
        "user": {"user_id": user.get("user_id"), "full_name": user.get("full_name")},
        "med": summary,
        "has_prescription": summary["medication_id"] in prescribed,
    }


def tool_schemas() -> list[dict[str, Any]]:
    # JSON schemas passed to OpenAI tool-calling (function tools).
    return [
        {
            "type": "function",
            "name": "get_medication",
            "description": "Fetch factual medication label info + rx_required + in_stock from the demo DB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Medication name (brand/generic/alias) or a sentence containing it."}
                },
                "required": ["query"],
            },
        },
        {
            "type": "function",
            "name": "get_user_prescriptions",
            "description": "Fetch the selected demo user's prescriptions list (med summaries).",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Demo user_id from the UI dropdown."}
                },
                "required": ["user_id"],
            },
        },
        {
            "type": "function",
            "name": "check_user_prescription",
            "description": "Check whether the selected demo user has a prescription for a specific medication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Demo user_id from the UI dropdown."},
                    "medication_query": {"type": "string", "description": "Medication name (brand/generic/alias) or a sentence containing it."},
                },
                "required": ["user_id", "medication_query"],
            },
        },
    ]