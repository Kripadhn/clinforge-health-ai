"""Per-patient clinical record routers, generated from the table registry."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..db import HAS_STOP, TABLES, one, query

router = APIRouter()
OPEN = "AND IFNULL(LENGTH(stop_at), 0) = 0"


@router.get("/patients")
def list_patients(
    q: Optional[str] = Query(None, description="Name substring"),
    gender: Optional[str] = None,
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    sql, params = "SELECT * FROM patients WHERE 1=1", []
    if q:
        sql += " AND (first_name LIKE ? OR last_name LIKE ?)"
        params += ["%" + q + "%"] * 2
    if gender:
        sql += " AND gender = ?"
        params.append(gender)
    sql += " ORDER BY last_name, first_name LIMIT ? OFFSET ?"
    return query(sql, tuple(params + [limit, offset]))


@router.get("/patients/{patient_id}")
def get_patient(patient_id: str) -> Dict[str, Any]:
    row = one("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if not row:
        raise HTTPException(404, "patient not found")
    return row


def _register(table: str, sort_col: str, filters: List[str]) -> None:
    def handler(
        patient_id: str,
        active: Optional[bool] = Query(None, description="Only open-ended records (no stop date)"),
        since: Optional[str] = Query(None, description="ISO date lower bound"),
        until: Optional[str] = Query(None, description="ISO date upper bound"),
        code: Optional[str] = None,
        extra: Optional[str] = Query(None, description="column=value; allowed: " + ", ".join(filters)),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> List[Dict[str, Any]]:
        sql, params = "SELECT * FROM %s WHERE patient_id = ?" % table, [patient_id]
        if code:
            if "code" not in filters:
                raise HTTPException(400, "code filter not supported for " + table)
            sql += " AND code = ?"
            params.append(code)
        if extra:
            col, _, val = extra.partition("=")
            if col not in filters:
                raise HTTPException(400, "unsupported filter column: " + col)
            sql += " AND %s = ?" % col
            params.append(val)
        if active:
            if table not in HAS_STOP:
                raise HTTPException(400, "active filter not supported for " + table)
            sql += " " + OPEN
        if since:
            sql += " AND %s >= ?" % sort_col
            params.append(since)
        if until:
            sql += " AND %s <= ?" % sort_col
            params.append(until)
        sql += " ORDER BY %s DESC LIMIT ? OFFSET ?" % sort_col
        return query(sql, tuple(params + [limit, offset]))

    router.add_api_route("/patients/{patient_id}/" + table, handler, methods=["GET"], name="list_" + table)


for _t, (_sort, _filters) in TABLES.items():
    _register(_t, _sort, _filters)


@router.get("/patients/{patient_id}/summary")
def patient_summary(patient_id: str) -> Dict[str, Any]:
    p = get_patient(patient_id)
    active = "SELECT id, code, description, start_at FROM %s WHERE patient_id=? " + OPEN + " ORDER BY start_at DESC"
    return {
        "patient": p,
        "active_conditions": query(active % "conditions", (patient_id,)),
        "active_medications": query(active % "medications", (patient_id,)),
        "allergies": query("SELECT id, code, description FROM allergies WHERE patient_id=?", (patient_id,)),
        "recent_encounters": query(
            "SELECT id, start_at, encounter_class, description FROM encounters WHERE patient_id=? "
            "ORDER BY start_at DESC LIMIT 5", (patient_id,)),
        "counts": {
            t: one("SELECT COUNT(*) AS n FROM %s WHERE patient_id=?" % t, (patient_id,))["n"] for t in TABLES
        },
    }


@router.get("/patients/{patient_id}/lab-trend")
def lab_trend(patient_id: str, code: str, limit: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    """Numeric observation series for one code, oldest first, with simple stats."""
    rows = query(
        "SELECT id, observed_at, value, units, description FROM observations "
        "WHERE patient_id=? AND code=? AND observation_type=? ORDER BY observed_at DESC LIMIT ?",
        (patient_id, code, "numeric", limit))
    rows.reverse()
    vals = []
    for r in rows:
        try:
            vals.append(float(r["value"]))
        except (TypeError, ValueError):
            pass
    stats = {"n": len(vals)}
    if vals:
        stats.update(min=min(vals), max=max(vals), first=vals[0], last=vals[-1], delta=vals[-1] - vals[0])
    return {"code": code, "series": rows, "stats": stats}


@router.get("/encounters/{encounter_id}")
def get_encounter(encounter_id: str) -> Dict[str, Any]:
    enc = one("SELECT * FROM encounters WHERE id=?", (encounter_id,))
    if not enc:
        raise HTTPException(404, "encounter not found")
    for t in ("conditions", "medications", "observations", "procedures"):
        enc[t] = query("SELECT * FROM %s WHERE encounter_id=?" % t, (encounter_id,))
    return enc


@router.get("/organizations")
def organizations(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> List[Dict[str, Any]]:
    return query("SELECT * FROM organizations ORDER BY name LIMIT ? OFFSET ?", (limit, offset))


@router.get("/providers")
def providers(specialty: Optional[str] = None, limit: int = Query(50, ge=1, le=200)) -> List[Dict[str, Any]]:
    if specialty:
        return query("SELECT * FROM providers WHERE specialty=? LIMIT ?", (specialty, limit))
    return query("SELECT * FROM providers LIMIT ?", (limit,))


@router.get("/observation-codes")
def observation_codes(q: str, limit: int = Query(10, ge=1, le=50)) -> List[Dict[str, Any]]:
    """Distinct observation codes whose description matches q (case-insensitive)."""
    return query(
        "SELECT code, description, units, COUNT(*) AS n FROM observations "
        "WHERE description LIKE ? GROUP BY code, description, units ORDER BY n DESC LIMIT ?",
        ("%" + q + "%", limit))
