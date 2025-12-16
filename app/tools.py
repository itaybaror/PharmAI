# app/tools.py
import logging

from app.db import MEDS, USERS_BY_ID, MEDS_BY_ID

logger = logging.getLogger("app.tools")


def _norm(s: str) -> str:
    """Normalize text for matching (lowercase + trim + collapse whitespace)."""
    return " ".join((s or "").strip().lower().split())


def _find_medication_in_text(text: str) -> dict | None:
    """Return the first MEDS entry whose brand/generic/alias appears in the given text (substring match)."""
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
    """Internal helper: return (user, error_dict). Tools use this to avoid repeating lookup logic."""
    uid = (user_id or "").strip()
    if not uid:
        return None, {"ok": False, "error_code": "MISSING_USER_ID"}

    user = USERS_BY_ID.get(uid)
    if not user:
        return None, {"ok": False, "error_code": "USER_NOT_FOUND"}

    return user, None


def _get_medication(query: str) -> tuple[dict | None, dict | None]:
    """Internal helper: return (med, error_dict) from free-text query."""
    q = (query or "").strip()
    if not q:
        return None, {"ok": False, "error_code": "MISSING_MEDICATION_QUERY"}

    med = _find_medication_in_text(q)
    if not med:
        return None, {"ok": False, "error_code": "MED_NOT_FOUND"}

    return med, None


def _med_summary(med: dict) -> dict:
    """Small shared med payload used by multiple workflows (keeps formatting consistent)."""
    return {
        "medication_id": med.get("medication_id"),
        "brand_name": med.get("brand_name"),
        "generic_name": med.get("generic_name"),
        "strength": med.get("strength"),
        "rx_required": bool(med.get("rx_required")),
        # Default True so meds without explicit in_stock behave as "available" in the demo.
        "in_stock": bool(med.get("in_stock", True)),
    }


def get_medication_by_name(query: str) -> dict:
    """
    Name: get_medication_by_name
    Purpose: Lookup a medication (brand/generic/alias) and return label-style facts for workflows.
    Inputs: query: str
    Output:
      - Success: {"ok": True, "med": {...}}
      - Failure: {"ok": False, "error_code": "..."}
    Error Handling: Uses structured error_code (no user-facing prose).
    Fallback: Substring match against brand/generic/aliases; first match wins.
    """
    logger.info("get_medication_by_name query=%r", query)

    med, err = _get_medication(query)
    if err:
        return err

    summary = _med_summary(med)
    display_name = f"{summary.get('brand_name', '')} ({summary.get('generic_name', '')}) {summary.get('strength', '')}".strip()

    return {
        "ok": True,
        "med": {
            "medication_id": summary["medication_id"],
            "name": display_name,
            "brand_name": summary["brand_name"],
            "generic_name": summary["generic_name"],
            "active_ingredients": med.get("active_ingredients", []),
            "form": med.get("form"),
            "strength": summary["strength"],
            "requires_prescription": summary["rx_required"],
            "dosage_instructions": med.get("usage_instructions"),
            "warnings": med.get("warnings"),
        },
    }


def get_medication_stock(query: str) -> dict:
    """
    Name: get_medication_stock
    Purpose: Check whether a medication is in stock (demo uses MEDS[].in_stock).
    Inputs: query: str
    Output:
      - Success: {"ok": True, "med": {...}}
      - Failure: {"ok": False, "error_code": "..."}
    Error Handling: Uses structured error_code (no user-facing prose).
    Fallback: Substring match against brand/generic/aliases; first match wins.
    """
    logger.info("get_medication_stock query=%r", query)

    med, err = _get_medication(query)
    if err:
        return err

    return {"ok": True, "med": _med_summary(med)}


def get_user_prescriptions(user_id: str) -> dict:
    """
    Name: get_user_prescriptions
    Purpose: Return the list of medications prescribed to a user.
    Inputs: user_id: str
    Output:
      - Success: {"ok": True, "user": {...}, "prescriptions": list[dict]}
      - Failure: {"ok": False, "error_code": "..."}
    Error Handling: Uses structured error_code (no user-facing prose).
    Fallback: Missing medication_id entries are skipped.
    """
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


def user_has_prescription(user_id: str, medication_query: str) -> dict:
    """
    Name: user_has_prescription
    Purpose: Check whether a user is prescribed a specific medication.
    Inputs: user_id: str, medication_query: str
    Output:
      - Success: {"ok": True, "has_prescription": bool, "med": {...}, "user": {...}}
      - Failure: {"ok": False, "error_code": "..."}
    Error Handling: Uses structured error_code (no user-facing prose).
    Fallback: Medication matching uses substring match; first match wins.
    """
    logger.info("user_has_prescription user_id=%r query=%r", user_id, medication_query)

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
        "has_prescription": summary["medication_id"] in prescribed,
        "med": summary,
        "user": {"user_id": user.get("user_id"), "full_name": user.get("full_name")},
    }