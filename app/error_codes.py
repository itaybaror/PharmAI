# app/error_codes.py
# Shared error codes used across tools + workflow handlers + responder.
# Keep these stable so your responder can reliably verbalize failures.

ERROR_HINTS: dict[str, str] = {
    # Generic
    "TOOL_ERROR": "The request failed for an unknown reason. Ask a short clarifying question or suggest retrying.",

    # User / auth / context
    "MISSING_USER_ID": "The user didn't select a demo user. Ask them to choose a user from the dropdown.",
    "USER_NOT_FOUND": "The selected demo user wasn't found. Ask them to choose a valid demo user from the dropdown.",

    # Medication query / resolution
    "MISSING_MEDICATION_QUERY": "The user didn't specify a medication. Ask which medication they mean.",
    "MED_NOT_FOUND": "The medication wasn't found in the demo database. Ask for a brand/generic name and give 1-2 examples.",

    # Routing / intent
    "NO_HANDLER": "No workflow handler exists for the detected intent. Apologize and ask what they want to do instead.",
    "UNKNOWN_INTENT": "The intent is unclear. Ask one short question to clarify what they want.",

    # Safety
    "NEEDS_CLINICIAN": "The user asked for personalized medical advice. Provide a brief safety response and recommend a clinician.",
}


def hint_for(code: str | None) -> str:
    """Return a short, responder-friendly hint for a given error code."""
    if not code:
        return ERROR_HINTS["TOOL_ERROR"]
    return ERROR_HINTS.get(code, ERROR_HINTS["TOOL_ERROR"])