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
        "description": "List the selected demo user's prescriptions (user is provided by the server).",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_user_prescription",
        "description": "Check if the selected demo user has a prescription for a medication in the demo DB (user is provided by the server).",
        "parameters": {
            "type": "object",
            "properties": {
                "medication_query": {"type": "string", "description": "Medication name, brand, or alias (free text)."},
            },
            "required": ["medication_query"],
            "additionalProperties": False,
        },
    },
]