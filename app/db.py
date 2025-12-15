# app/db.py

MEDS = [
    {
        "medication_id": "m001",
        "brand_name": "Tylenol",
        "generic_name": "Paracetamol",
        "active_ingredients": ["Paracetamol"],
        "form": "tablet",
        "strength": "500mg",
        "rx_required": False,
        "usage_instructions": "Adults: 500–1000 mg every 4–6 hours as needed. Max 4000 mg/day.",
        "warnings": "Avoid exceeding the maximum daily dose.",
        "aliases": ["acetaminophen", "panadol"],
    },
    {
        "medication_id": "m002",
        "brand_name": "Advil",
        "generic_name": "Ibuprofen",
        "active_ingredients": ["Ibuprofen"],
        "form": "tablet",
        "strength": "200mg",
        "rx_required": False,
        "usage_instructions": "Adults: 200–400 mg every 6–8 hours with food as needed. Max 1200 mg/day OTC.",
        "warnings": "May irritate the stomach.",
        "aliases": ["nurofen"],
    },
]