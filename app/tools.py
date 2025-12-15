# app/tools.py
import logging
from app.db import MEDS

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

        for a in med.get("aliases", []):
            aa = _norm(a)
            if aa and aa in t:
                return med

    return None


def resolve_medication_from_text(text: str) -> str | None:
    med = _find_medication_in_text(text)
    if not med:
        return None
    name = (med.get("generic_name") or med.get("brand_name") or "").strip()
    return name if name else None


def get_medication_by_name(query: str) -> dict:
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