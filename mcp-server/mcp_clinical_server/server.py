"""MCP server (Streamable HTTP at /mcp, port 8002). Token comes from the Authorization: Bearer header."""
import json
import os
from typing import Optional

from clinical_shared.ehr import AuthError, EHRApi
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .tools import ClinicalTools

mcp = FastMCP("clinforge-ehr", host=os.environ.get("MCP_HOST", "0.0.0.0"),
              port=int(os.environ.get("MCP_PORT", "8002")), stateless_http=True)
_tools = None  # built lazily so importing the module needs no network


def tools() -> ClinicalTools:
    global _tools
    if _tools is None:
        _tools = ClinicalTools(EHRApi())
    return _tools


def _token(ctx: Context) -> Optional[str]:
    req = ctx.request_context.request
    auth = req.headers.get("authorization", "") if req is not None else ""
    return auth[7:].strip() if auth.lower().startswith("bearer ") else None


def _run(name: str, ctx: Context, *args):
    try:
        return json.dumps(getattr(tools(), name)(_token(ctx), *args), default=str)
    except AuthError as e:
        raise ToolError("access denied: %s" % e)


@mcp.tool()
def list_my_patients(ctx: Context) -> str:
    """Patients assigned to the signed-in clinician."""
    return _run("list_my_patients", ctx)


@mcp.tool()
def get_patient_summary(patient_id: str, ctx: Context) -> str:
    """Demographics, active conditions/medications, allergies, recent encounters."""
    return _run("get_patient_summary", ctx, patient_id)


@mcp.tool()
def list_conditions(patient_id: str, ctx: Context, active_only: bool = True) -> str:
    """Conditions for a patient (active only by default)."""
    return _run("list_conditions", ctx, patient_id, active_only)


@mcp.tool()
def list_medications(patient_id: str, ctx: Context, active_only: bool = True) -> str:
    """Medications for a patient (active only by default)."""
    return _run("list_medications", ctx, patient_id, active_only)


@mcp.tool()
def list_careplans(patient_id: str, ctx: Context, active_only: bool = True) -> str:
    """Care plans for a patient."""
    return _run("list_careplans", ctx, patient_id, active_only)


@mcp.tool()
def list_observations(patient_id: str, ctx: Context, code: Optional[str] = None,
                      since: Optional[str] = None, limit: int = 50) -> str:
    """Observations, optionally filtered by code and start date."""
    return _run("list_observations", ctx, patient_id, code, since, limit)


@mcp.tool()
def list_encounters(patient_id: str, ctx: Context, since: Optional[str] = None, limit: int = 500) -> str:
    """Encounters for a patient (newest first), optionally since an ISO date."""
    return _run("list_encounters", ctx, patient_id, since, limit)


@mcp.tool()
def list_claims(patient_id: str, ctx: Context, status: Optional[str] = None) -> str:
    """Claims for a patient, optionally filtered by claim status."""
    return _run("list_claims", ctx, patient_id, status)


@mcp.tool()
def get_lab_trend(patient_id: str, code: str, ctx: Context) -> str:
    """Numeric observation series and stats for one observation code."""
    return _run("get_lab_trend", ctx, patient_id, code)


@mcp.tool()
def get_patient_coverage(patient_id: str, ctx: Context) -> str:
    """Insurance coverage history for a patient."""
    return _run("get_patient_coverage", ctx, patient_id)


@mcp.tool()
def get_encounter(encounter_id: str, ctx: Context) -> str:
    """Encounter with linked conditions, medications, observations, procedures."""
    return _run("get_encounter", ctx, encounter_id)


@mcp.tool()
def find_observation_code(query: str, ctx: Context) -> str:
    """Find observation codes by name, for example hemoglobin A1c."""
    return _run("find_observation_code", ctx, query)


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
