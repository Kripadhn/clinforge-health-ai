"""Structured data endpoints for the apps/ views. Same security path as /chat: MCP tools only."""
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from .mcp_client import MCPCaller, ToolDenied

router = APIRouter(prefix="/views")


def _caller(authorization: Optional[str]) -> MCPCaller:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    return MCPCaller(authorization[7:].strip())


async def _call(caller: MCPCaller, tool: str, **args):
    try:
        return await caller.call(tool, **args)
    except ToolDenied as e:
        raise HTTPException(403, str(e))


@router.get("/patients")
async def patients(authorization: Optional[str] = Header(None)) -> list:
    return await _call(_caller(authorization), "list_my_patients")


@router.get("/lab-trend")
async def lab_trend(patient_id: str, q: str, authorization: Optional[str] = Header(None)) -> dict:
    caller = _caller(authorization)
    codes = await _call(caller, "find_observation_code", query=q)
    if not codes:
        raise HTTPException(404, "no observation code matches: " + q)
    trend = await _call(caller, "get_lab_trend", patient_id=patient_id, code=codes[0]["code"])
    return {"query": q, "code": codes[0]["code"], "description": codes[0]["description"],
            "units": codes[0]["units"], "matches": codes[:5], **trend}


@router.get("/timeline")
async def timeline(patient_id: str, since: Optional[str] = None,
                   authorization: Optional[str] = Header(None)) -> dict:
    caller = _caller(authorization)
    rows = await _call(caller, "list_encounters", patient_id=patient_id, since=since)
    return {"patient_id": patient_id,
            "encounters": [{"id": r["id"], "start_at": r["start_at"], "stop_at": r["stop_at"],
                            "encounter_class": r["encounter_class"], "description": r["description"],
                            "reason": r["reason_description"]} for r in rows]}
