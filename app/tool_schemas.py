# app/tool_schemas.py
from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_medication",
        "description": "Fetch factual medication info (label facts), prescription requirement, and stock from the demo DB.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Medication name, brand, or alias (free text)."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_user_prescriptions",
        "description": "List a demo user's prescriptions (resolved to medication summaries) from the demo DB.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Demo user id like 'u001'."},
            },
            "required": ["user_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_user_prescription",
        "description": "Check if a demo user has a prescription for a medication in the demo DB.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Demo user id like 'u001'."},
                "medication_query": {"type": "string", "description": "Medication name, brand, or alias (free text)."},
            },
            "required": ["user_id", "medication_query"],
            "additionalProperties": False,
        },
    },
]