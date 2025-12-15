# app/workflows/__init__.py
from app.workflows.med_lookup import handle as med_lookup
from app.workflows.stock_check import handle as stock_check
from app.workflows.prescription_check import handle as prescription_check

ROUTES = {
    "MED_LOOKUP": med_lookup,
    "STOCK_CHECK": stock_check,
    "PRESCRIPTION_CHECK": prescription_check,
}