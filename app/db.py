# app/db.py
# Synthetic in-memory "database" for the assignment:
# - 10 users
# - 5 medications
# - each user has a list of prescribed medications (by medication_id)

USERS = [
    {"user_id": "u001", "full_name": "Noa Cohen", "email": "noa.cohen@example.com", "prescribed_medications": ["m003", "m005"]},
    {"user_id": "u002", "full_name": "Itai Levi", "email": "itai.levi@example.com", "prescribed_medications": ["m004"]},
    {"user_id": "u003", "full_name": "Maya Rosen", "email": "maya.rosen@example.com", "prescribed_medications": ["m005"]},
    {"user_id": "u004", "full_name": "Daniel Katz", "email": "daniel.katz@example.com", "prescribed_medications": ["m003", "m004"]},
    {"user_id": "u005", "full_name": "Yael Friedman", "email": "yael.friedman@example.com", "prescribed_medications": ["m005"]},
    {"user_id": "u006", "full_name": "Amit Shalev", "email": "amit.shalev@example.com", "prescribed_medications": ["m004"]},
    {"user_id": "u007", "full_name": "Shira Bar", "email": "shira.bar@example.com", "prescribed_medications": ["m003"]},
    {"user_id": "u008", "full_name": "Omer Azulay", "email": "omer.azulay@example.com", "prescribed_medications": ["m005", "m004"]},
    {"user_id": "u009", "full_name": "Lior Ben-David", "email": "lior.bendavid@example.com", "prescribed_medications": ["m003"]},
    {"user_id": "u010", "full_name": "Tamar Gold", "email": "tamar.gold@example.com", "prescribed_medications": ["m004", "m005"]},
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
        "brand_name": "Amoxicillin",
        "generic_name": "Amoxicillin",
        "active_ingredients": ["Amoxicillin"],
        "form": "capsule",
        "strength": "500mg",
        "rx_required": True,
        "usage_instructions": "Prescription-only: take exactly as directed; finish the full course unless told otherwise.",
        "warnings": "Possible allergic reactions; seek urgent care if rash, swelling, or breathing issues occur.",
        "aliases": ["amoxil"],
        "in_stock": True,
    },
    {
        "medication_id": "m005",
        "brand_name": "Augmentin",
        "generic_name": "Amoxicillin/Clavulanate",
        "active_ingredients": ["Amoxicillin", "Clavulanate"],
        "form": "tablet",
        "strength": "875mg/125mg",
        "rx_required": True,
        "usage_instructions": "Prescription-only: follow the dosing instructions provided by the prescriber.",
        "warnings": "May cause gastrointestinal upset; seek medical help for signs of allergic reaction.",
        "aliases": ["co-amoxiclav"],
        "in_stock": False,
    },
]

# Indexes for fast lookups (keep USERS/MEDS lists for readability + UI ordering)
USERS_BY_ID = {u["user_id"]: u for u in USERS}
MEDS_BY_ID = {m["medication_id"]: m for m in MEDS}