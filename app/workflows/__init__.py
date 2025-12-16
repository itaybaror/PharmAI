# app/workflows/__init__.py
from app.workflows.med_lookup import handle as med_lookup
from app.workflows.user_prescriptions import handle as user_prescriptions
from app.workflows.stock_check import handle as stock_check

ROUTES = {
    "MED_LOOKUP": med_lookup,
    "USER_PRESCRIPTIONS": user_prescriptions,
    "STOCK_CHECK": stock_check,
}