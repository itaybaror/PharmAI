# app/tools.py
import logging
from typing import Any, Literal

from app.db import MEDS, USERS_BY_ID, MEDS_BY_ID

logger = logging.getLogger("app.tools")


# ----------------------------
# Tool schemas (Responses API)
# NOTE: user_id is passed by the server (UI dropdown). The model should not guess it.
# Strict mode notes:
# - strict=true
# - additionalProperties=false
# - all properties must be required (use null type to represent "optional")
# ----------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_medication",
        "description": "Fetch factual medication info (label facts), prescription requirement, and stock from the demo DB.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Medication name, brand, or alias (free text).",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_user_prescriptions",
        "description": "List the selected demo user's prescriptions (user is provided by the server).",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_medications",
        "description": "List medications available in the demo pharmacy database, with optional filters for Rx requirement and stock status.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "rx_filter": {
                    "type": ["string", "null"],
                    "enum": ["rx", "non_rx", "both", None],
                    "description": "Filter by prescription requirement. Use null to mean default (both).",
                },
                "stock_filter": {
                    "type": ["string", "null"],
                    "enum": ["in_stock", "out_of_stock", "both", None],
                    "description": "Filter by stock status. Use null to mean default (both).",
                },
            },
            "required": ["rx_filter", "stock_filter"],
            "additionalProperties": False,
        },
    },
]


def _norm(s: str) -> str:
    """Lowercase + trim + collapse whitespace."""
    return " ".join((s or "").strip().lower().split())


def _find_medication_in_text(text: str) -> dict | None:
    """Return the first medication whose brand/generic/alias appears in text (substring match)."""
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
    """Resolve a demo user by id; returns (user, error_dict)."""
    uid = (user_id or "").strip()
    if not uid:
        return None, {"ok": False, "error_code": "MISSING_USER_ID"}

    user = USERS_BY_ID.get(uid)
    if not user:
        return None, {"ok": False, "error_code": "USER_NOT_FOUND"}

    return user, None


def _get_medication(query: str) -> tuple[dict | None, dict | None]:
    """Resolve a demo medication from free-text; returns (med, error_dict)."""
    q = (query or "").strip()
    if not q:
        return None, {"ok": False, "error_code": "MISSING_MEDICATION_QUERY"}

    med = _find_medication_in_text(q)
    if not med:
        return None, {"ok": False, "error_code": "MED_NOT_FOUND"}

    return med, None


def _med_summary(med: dict) -> dict:
    """Common med summary payload used by tools."""
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
    """
    Tool: get_medication
    Purpose: Return factual medication data from the demo DB (ingredients, warnings, dosage text, Rx requirement, stock).
    Returns:
      - {"ok": True, "med": {...}}
      - {"ok": False, "error_code": "..."}
    """
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
    """
    Tool: get_user_prescriptions
    Purpose: Return the selected demo user's prescriptions as medication summaries.
    Returns:
      - {"ok": True, "user": {...}, "prescriptions": [...]}
      - {"ok": False, "error_code": "..."}
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


def list_medications(
    rx_filter: Literal["rx", "non_rx", "both"] | None = None,
    stock_filter: Literal["in_stock", "out_of_stock", "both"] | None = None,
) -> dict:
    """
    Tool: list_medications
    Purpose: List medications in the demo DB with optional filters.
      - rx_filter: rx / non_rx / both (or None => both)
      - stock_filter: in_stock / out_of_stock / both (or None => both)
    """
    rx_filter = rx_filter or "both"
    stock_filter = stock_filter or "both"
    logger.info("list_medications rx_filter=%s stock_filter=%s", rx_filter, stock_filter)

    def _rx_ok(m: dict) -> bool:
        rx = bool(m.get("rx_required"))
        return True if rx_filter == "both" else (rx if rx_filter == "rx" else (not rx))

    def _stock_ok(m: dict) -> bool:
        st = bool(m.get("in_stock", True))
        return True if stock_filter == "both" else (st if stock_filter == "in_stock" else (not st))

    meds: list[dict] = []
    for med in MEDS:
        summary = _med_summary(med)
        if _rx_ok(summary) and _stock_ok(summary):
            meds.append(summary)

    return {"ok": True, "medications": meds}