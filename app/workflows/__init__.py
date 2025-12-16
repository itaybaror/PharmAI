# app/workflows/__init__.py
from app.workflows.med_lookup import handle as med_lookup
from app.workflows.user_prescriptions import handle as user_prescriptions

ROUTES = {
    "MED_LOOKUP": med_lookup,
    "USER_PRESCRIPTIONS": user_prescriptions,
    "STOCK_CHECK": lambda intent, last_user, conversation, user_id: {
        "assistant": "STOCK_CHECK workflow not implemented yet.",
        "intent": intent.model_dump(),
    },
    "PRESCRIPTION_CHECK": lambda intent, last_user, conversation, user_id: {
        "assistant": "PRESCRIPTION_CHECK workflow not implemented yet.",
        "intent": intent.model_dump(),
    },
}