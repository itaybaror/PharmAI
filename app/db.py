# app/db.py
# Synthetic in-memory "database" for the assignment:
# - 10 users
# - 5 medications
# - each user has a list of prescribed medications (by medication_id)

USERS = [
    {"user_id": "u001", "full_name": "Noa Cohen", "prescribed_medications": ["m003", "m005"]},
    {"user_id": "u002", "full_name": "Itai Levi", "prescribed_medications": ["m004"]},
    {"user_id": "u003", "full_name": "Maya Rosen", "prescribed_medications": ["m005"]},
    {"user_id": "u004", "full_name": "Daniel Katz", "prescribed_medications": ["m003", "m004"]},
    {"user_id": "u005", "full_name": "Yael Friedman", "prescribed_medications": []},
    {"user_id": "u006", "full_name": "Amit Shalev", "prescribed_medications": ["m004"]},
    {"user_id": "u007", "full_name": "Shira Bar", "prescribed_medications": ["m003"]},
    {"user_id": "u008", "full_name": "Omer Azulay", "prescribed_medications": ["m005", "m004"]},
    {"user_id": "u009", "full_name": "Lior Ben-David", "prescribed_medications": ["m003"]},
    {"user_id": "u010", "full_name": "Tamar Gold", "prescribed_medications": ["m004", "m005"]},
]

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
        "in_stock": True,
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
        "in_stock": True,
    },
    {
        "medication_id": "m003",
        "brand_name": "Zoloft",
        "generic_name": "Sertraline",
        "active_ingredients": ["Sertraline"],
        "form": "tablet",
        "strength": "50mg",
        "rx_required": True,
        "usage_instructions": "Prescription-only: follow the dosing instructions provided by the prescriber.",
        "warnings": "Do not stop abruptly without medical guidance; seek help for severe side effects.",
        "aliases": [],
        "in_stock": True,
    },
    {
        "medication_id": "m004",
        "brand_name": "Lipitor",
        "generic_name": "Atorvastatin",
        "active_ingredients": ["Atorvastatin"],
        "form": "tablet",
        "strength": "20mg",
        "rx_required": True,
        "usage_instructions": "Prescription-only: take exactly as directed by the prescriber.",
        "warnings": "Seek medical help for severe muscle pain/weakness, dark urine, or signs of liver problems.",
        "aliases": ["atorvastatin"],
        "in_stock": True,
    },
    {
        "medication_id": "m005",
        "brand_name": "Zestril",
        "generic_name": "Lisinopril",
        "active_ingredients": ["Lisinopril"],
        "form": "tablet",
        "strength": "10mg",
        "rx_required": True,
        "usage_instructions": "Prescription-only: take exactly as directed by the prescriber.",
        "warnings": "Seek urgent care for swelling of face/lips/tongue, trouble breathing, or severe dizziness.",
        "aliases": ["lisinopril", "prinivil"],
        "in_stock": False,
    },
]

# Indexes for fast lookups (keep USERS/MEDS lists for readability + UI ordering)
USERS_BY_ID = {u["user_id"]: u for u in USERS}
MEDS_BY_ID = {m["medication_id"]: m for m in MEDS}