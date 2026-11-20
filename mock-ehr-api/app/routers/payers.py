"""Payer and coverage routes (payer, insurer master and plans joined)."""
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..db import one, query

router = APIRouter()


@router.get("/payers")
def list_payers() -> List[Dict[str, Any]]:
    return query(
        "SELECT p.id, p.name, p.unique_customers, p.revenue, x.company_id, c.ownership "
        "FROM payers p LEFT JOIN payer_crosswalk x ON x.payer_id = p.id "
        "LEFT JOIN insurance_companies c ON c.id = x.company_id ORDER BY p.name")


@router.get("/payers/{payer_id}")
def get_payer(payer_id: str) -> Dict[str, Any]:
    p = one("SELECT * FROM payers WHERE id = ?", (payer_id,))
    if not p:
        raise HTTPException(404, "payer not found")
    x = one("SELECT company_id FROM payer_crosswalk WHERE payer_id = ?", (payer_id,))
    cid = x["company_id"] if x else None
    p["insurer"] = one("SELECT * FROM insurance_companies WHERE id = ?", (cid,)) if cid else None
    p["plans"] = query("SELECT * FROM insurance_plans WHERE payer_id = ? ORDER BY plan_id", (cid,)) if cid else []
    return p


@router.get("/patients/{patient_id}/coverage")
def patient_coverage(patient_id: str) -> Dict[str, Any]:
    if not one("SELECT 1 AS ok FROM patients WHERE id = ?", (patient_id,)):
        raise HTTPException(404, "patient not found")
    history = query(
        "SELECT t.start_year, t.end_year, t.payer_id, p.name AS payer_name, t.ownership "
        "FROM payer_transitions t JOIN payers p ON p.id = t.payer_id "
        "WHERE t.patient_id = ? ORDER BY t.start_year", (patient_id,))
    return {"patient_id": patient_id, "history": history}
