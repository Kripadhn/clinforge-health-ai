"""Session introspection: maps a care-team token to a clinician and the patients they may access."""
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..db import one, query

router = APIRouter()


@router.get("/sessions/introspect")
def introspect(token: str) -> Dict[str, Any]:
    s = one("SELECT * FROM care_sessions WHERE token = ?", (token,))
    if not s:
        raise HTTPException(401, "unknown token")
    if s["expires_at"] <= datetime.now(timezone.utc).isoformat():
        raise HTTPException(401, "token expired")
    pts = [r["patient_id"] for r in query(
        "SELECT patient_id FROM care_session_patients WHERE token = ? ORDER BY patient_id", (token,))]
    return {"active": True, "clinician_id": s["clinician_id"], "name": s["name"],
            "role": s["role"], "patient_ids": pts, "expires_at": s["expires_at"]}
