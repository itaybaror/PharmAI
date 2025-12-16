# app/tools.py
import logging
from app.db import MEDS, USERS

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


def _get_user_by_id(user_id: str) -> dict | None:
    """Return a user dict from USERS by user_id."""
    uid = (user_id or "").strip()
    if not uid:
        return None
    for u in USERS:
        if u.get("user_id") == uid:
            return u
    return None


def _med_summary(med: dict) -> dict:
    """Small shared med payload used by prescriptions + stock."""
    return {
        "medication_id": med.get("medication_id"),
        "brand_name": med.get("brand_name"),
        "generic_name": med.get("generic_name"),
        "strength": med.get("strength"),
        "rx_required": bool(med.get("rx_required")),
    }


def _med_display_name(med: dict) -> str:
    """Consistent display name for UI replies."""
    return f"{med.get('brand_name', '')} ({med.get('generic_name', '')}) {med.get('strength', '')}".strip()


def get_medication_by_name(query: str) -> dict:
    """
    Name: get_medication_by_name
    Purpose: Lookup a medication (brand/generic/alias) and return label-style facts for workflows.
    Inputs: query: str
    Output: dict
      - Success: {"found": True, "med": {...}}
      - Failure: {"found": False, "message": str}
    Error Handling: No match -> found=False with message.
    Fallback: Accepts sentences; substring match against brand/generic/aliases; first match wins.
    """
    logger.info("get_medication_by_name query=%r", query)

    med = _find_medication_in_text(query)
    if not med:
        return {
            "found": False,
            "message": (
                f"I couldn't find a medication matching '{query}'. "
                "Try a brand or generic name (e.g., 'Advil', 'Ibuprofen', 'Tylenol')."
            ),
        }

    return {
        "found": True,
        "med": {
            "medication_id": med.get("medication_id"),
            "name": _med_display_name(med),
            "brand_name": med.get("brand_name"),
            "generic_name": med.get("generic_name"),
            "active_ingredients": med.get("active_ingredients", []),
            "form": med.get("form"),
            "strength": med.get("strength"),
            "requires_prescription": bool(med.get("rx_required")),
            "dosage_instructions": med.get("usage_instructions"),
            "warnings": med.get("warnings"),
        },
    }


def get_medication_stock(query: str) -> dict:
    """
    Name: get_medication_stock
    Purpose: Check whether a medication is in stock (demo uses MEDS[].in_stock).
    Inputs: query: str
    Output: dict
      - Success: {"found": True, "med": {...}, "in_stock": bool}
      - Failure: {"found": False, "message": str}
    Error Handling: No match -> found=False with message.
    Fallback: Substring match against brand/generic/aliases; first match wins.
    """
    logger.info("get_medication_stock query=%r", query)

    med = _find_medication_in_text(query)
    if not med:
        return {
            "found": False,
            "message": (
                f"I couldn't find a medication matching '{query}'. "
                "Try a brand or generic name (e.g., 'Augmentin', 'Amoxicillin')."
            ),
        }

    # Default True so meds without explicit in_stock behave as "available" in the demo.
    return {
        "found": True,
        "med": _med_summary(med),
        "in_stock": bool(med.get("in_stock", True)),
    }


def get_user_prescriptions(user_id: str) -> dict:
    """
    Name: get_user_prescriptions
    Purpose: Return the list of medications prescribed to a user.
    Inputs: user_id: str
    Output: dict
      - Success: {"found_user": True, "user": {...}, "prescriptions": list[dict]}
      - Failure: {"found_user": False, "message": str}
    Error Handling: Unknown user -> found_user=False with message.
    Fallback: Missing medication_id entries are skipped.
    """
    logger.info("get_user_prescriptions user_id=%r", user_id)

    user = _get_user_by_id(user_id)
    if not user:
        return {"found_user": False, "message": "Unknown demo user. Please select a user from the dropdown."}

    meds_by_id = {m.get("medication_id"): m for m in MEDS}
    prescriptions: list[dict] = []

    for mid in (user.get("prescribed_medications") or []):
        m = meds_by_id.get(mid)
        if m:
            prescriptions.append(_med_summary(m))

    return {
        "found_user": True,
        "user": {"user_id": user.get("user_id"), "full_name": user.get("full_name")},
        "prescriptions": prescriptions,
    }


def user_has_prescription(user_id: str, medication_query: str) -> dict:
    """
    Name: user_has_prescription
    Purpose: Check whether a user is prescribed a specific medication.
    Inputs: user_id: str, medication_query: str
    Output: dict
      - Success: {"found_user": True, "found_med": True, "has_prescription": bool, "med": {...}}
      - Failure (no user): {"found_user": False, "message": str}
      - Failure (no med): {"found_user": True, "found_med": False, "message": str}
    Error Handling: Unknown user -> found_user=False. Unknown med -> found_med=False.
    Fallback: Substring match against brand/generic/aliases; first match wins.
    """
    logger.info("user_has_prescription user_id=%r query=%r", user_id, medication_query)

    user = _get_user_by_id(user_id)
    if not user:
        return {"found_user": False, "message": "Unknown demo user. Please select a user from the dropdown."}

    med = _find_medication_in_text(medication_query)
    if not med:
        return {
            "found_user": True,
            "found_med": False,
            "message": "I couldn't find that medication in the demo database. Try a brand or generic name.",
        }

    prescribed = set(user.get("prescribed_medications") or [])
    mid = med.get("medication_id")

    return {
        "found_user": True,
        "found_med": True,
        "has_prescription": mid in prescribed,
        "med": _med_summary(med),
    }