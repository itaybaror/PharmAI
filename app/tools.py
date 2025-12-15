# app/tools.py
import logging
from app.db import MEDS

logger = logging.getLogger("app.tools")


def _norm(s: str) -> str:
    """Normalize text for matching (lowercase + trim + collapse whitespace)."""
    # (s or "") ensures we can safely call string methods even if s is None
    # split() breaks on any whitespace; " ".join(...) collapses multiple spaces into one
    return " ".join((s or "").strip().lower().split())


def _find_medication_in_text(text: str) -> dict | None:
    """Return the first MEDS entry whose brand/generic/alias appears in the given text (substring match)."""
    t = _norm(text)
    if not t:
        return None

    for med in MEDS:
        # Normalize candidate names so comparisons are case/whitespace-insensitive
        brand = _norm(med.get("brand_name", ""))
        generic = _norm(med.get("generic_name", ""))

        # Substring match lets us handle full sentences like "what are warnings for ibuprofen?"
        if brand and brand in t:
            return med
        if generic and generic in t:
            return med

        # Also allow matching known aliases (e.g., common shorthand or alternate brand names)
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
      - Success: {"found": True, "med": {"medication_id": any|None, "name": str, "brand_name": str|None, "generic_name": str|None,
                                         "active_ingredients": list[str], "form": str|None, "strength": str|None,
                                         "requires_prescription": bool, "dosage_instructions": str|None, "warnings": str|None}}
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

    display_name = (
        f"{med.get('brand_name', '')} ({med.get('generic_name', '')}) {med.get('strength', '')}"
    ).strip()

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