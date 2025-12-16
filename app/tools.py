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

        for a in med.get("aliases", []):
            aa = _norm(a)
            if aa and aa in t:
                return med

    return None


def resolve_medication_from_text(text: str) -> str | None:
    """
    Name: resolve_medication_from_text
    Purpose: Extract a medication name from free text (generic preferred) to support multi-turn follow-ups.
    Inputs: text: str
    Output: str | None (generic_name/brand_name if found; otherwise None)
    Error Handling: Returns None on empty/unmatched text; does not raise exceptions for normal input.
    Fallback: Substring match over brand_name/generic_name/aliases via _find_medication_in_text; first match wins.
    """
    med = _find_medication_in_text(text)
    if not med:
        return None
    name = (med.get("generic_name") or med.get("brand_name") or "").strip()
    return name if name else None


def get_medication_by_name(query: str) -> dict:
    """
    Name: get_medication_by_name
    Purpose: Lookup a medication (brand/generic/alias) in MEDS and return label-style facts for agent workflows.
    Inputs: query: str
    Output: dict
      - Success: {"found": True, "med": {...}}
      - Failure: {"found": False, "message": str}
    Error Handling: If no match, returns {"found": False, "message": str}; does not raise exceptions for normal user input.
    Fallback: Accepts sentences; matches by substring against brand_name/generic_name/aliases; returns first match in MEDS.
    """
    logger.info("get_medication_by_name query=%r", query)

    med = _find_medication_in_text(query)
    if not med:
        logger.info("no match query=%r", query)
        return {
            "found": False,
            "message": (
                f"I couldn't find a medication matching '{query}'. "
                "Try a brand or generic name (e.g., 'Advil', 'Ibuprofen', 'Tylenol')."
            ),
        }

    logger.info("matched brand=%r generic=%r", med.get("brand_name"), med.get("generic_name"))

    display_name = f"{med.get('brand_name', '')} ({med.get('generic_name', '')}) {med.get('strength', '')}".strip()

    return {
        "found": True,
        "med": {
            "medication_id": med.get("medication_id"),
            "name": display_name,
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


def get_user_by_id(user_id: str) -> dict | None:
    """Find a user record in USERS by user_id."""
    uid = (user_id or "").strip()
    if not uid:
        return None
    for u in USERS:
        if u.get("user_id") == uid:
            return u
    return None


def get_user_prescriptions(user_id: str) -> dict:
    """
    Name: get_user_prescriptions
    Purpose: Return the list of medications prescribed to a user (by user_id).
    Inputs: user_id: str
    Output: dict
      - Success: {"found_user": True, "user": {"user_id": str, "full_name": str}, "prescriptions": list[dict]}
      - Failure: {"found_user": False, "message": str}
    Error Handling: If user_id is missing/unknown, returns found_user=False with a message.
    Fallback: Returns an empty prescriptions list if the user exists but has none.
    """
    logger.info("get_user_prescriptions user_id=%r", user_id)

    user = get_user_by_id(user_id)
    if not user:
        return {
            "found_user": False,
            "message": "Unknown demo user. Please select a user from the dropdown.",
        }

    ids = list(user.get("prescribed_medications") or [])
    meds_by_id = {m.get("medication_id"): m for m in MEDS}

    prescriptions: list[dict] = []
    for mid in ids:
        m = meds_by_id.get(mid)
        if not m:
            continue
        prescriptions.append(
            {
                "medication_id": m.get("medication_id"),
                "brand_name": m.get("brand_name"),
                "generic_name": m.get("generic_name"),
                "strength": m.get("strength"),
                "rx_required": bool(m.get("rx_required")),
            }
        )

    return {
        "found_user": True,
        "user": {"user_id": user.get("user_id"), "full_name": user.get("full_name")},
        "prescriptions": prescriptions,
    }


def user_has_prescription(user_id: str, medication_query: str) -> dict:
    """
    Name: user_has_prescription
    Purpose: Check whether a user is prescribed a specific medication (by name/alias in text).
    Inputs: user_id: str, medication_query: str
    Output: dict
      - Success: {"found_user": True, "found_med": True, "has_prescription": bool, "med": {...}}
      - Failure (no user): {"found_user": False, "message": str}
      - Failure (no med): {"found_user": True, "found_med": False, "message": str}
    Error Handling: Unknown user -> found_user=False. Unknown medication -> found_med=False.
    Fallback: Medication matching uses substring match against brand/generic/aliases; first match wins.
    """
    logger.info("user_has_prescription user_id=%r query=%r", user_id, medication_query)

    user = get_user_by_id(user_id)
    if not user:
        return {
            "found_user": False,
            "message": "Unknown demo user. Please select a user from the dropdown.",
        }

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
        "med": {
            "medication_id": mid,
            "brand_name": med.get("brand_name"),
            "generic_name": med.get("generic_name"),
            "strength": med.get("strength"),
            "rx_required": bool(med.get("rx_required")),
        },
    }


def get_medication_stock(query: str) -> dict:
    """
    Name: get_medication_stock
    Purpose: Check whether a medication is currently in stock (and whether pickup today is possible).
    Inputs: query: str
    Output: dict
      - Success: {"found": True, "med": {"medication_id": str|None, "brand_name": str|None, "generic_name": str|None, "strength": str|None},
                 "in_stock": bool, "can_pickup_today": bool}
      - Failure: {"found": False, "message": str}
    Error Handling: If medication cannot be resolved from query, returns found=False with message.
    Fallback: Matches by substring against brand/generic/aliases; first match wins.
    """
    logger.info("get_medication_stock query=%r", query)

    med = _find_medication_in_text(query)
    if not med:
        return {
            "found": False,
            "message": (
                f"I couldn't find a medication matching '{query}'. "
                "Try a brand or generic name (e.g., 'Advil', 'Ibuprofen', 'Zoloft')."
            ),
        }

    # For the demo, stock is stored on the med record in db.py (you'll add e.g. in_stock: True/False).
    in_stock = bool(med.get("in_stock", True))
    can_pickup_today = in_stock

    return {
        "found": True,
        "med": {
            "medication_id": med.get("medication_id"),
            "brand_name": med.get("brand_name"),
            "generic_name": med.get("generic_name"),
            "strength": med.get("strength"),
            "rx_required": bool(med.get("rx_required")),
        },
        "in_stock": in_stock,
        "can_pickup_today": can_pickup_today,
    }