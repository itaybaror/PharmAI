# app/tools.py
from typing import Optional

# MEDS lives in db.py at the project root
from app.db import MEDS


def _normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _find_medication(query: str) -> Optional[dict]:
    q = _normalize(query)
    if not q:
        return None

    for med in MEDS:
        if q in _normalize(med["brand_name"]) or q in _normalize(med["generic_name"]):
            return med

    for med in MEDS:
        for a in med.get("aliases", []):
            if q in _normalize(a):
                return med

    return None


def get_medication_by_name(query: str) -> dict:
    """Tool: return factual, label-style medication info from an in-memory dataset."""
    med = _find_medication(query)
    if not med:
        return {
            "found": False,
            "message": (
                f"I couldn't find a medication matching '{query}'. "
                "Try a brand or generic name (e.g., 'Advil', 'Ibuprofen', 'Tylenol')."
            ),
        }

    display_name = f"{med['brand_name']} ({med['generic_name']}) {med['strength']}".strip()

    return {
        "found": True,
        "med": {
            "medication_id": med["medication_id"],
            "name": display_name,
            "brand_name": med["brand_name"],
            "generic_name": med["generic_name"],
            "active_ingredients": med["active_ingredients"],
            "form": med["form"],
            "strength": med["strength"],
            "requires_prescription": bool(med["rx_required"]),
            "dosage_instructions": med["usage_instructions"],
            "warnings": med["warnings"],
        },
    }