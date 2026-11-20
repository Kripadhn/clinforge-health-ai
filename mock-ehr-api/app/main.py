"""ClinForge mock EHR: read-only API over synthetic clinical data."""
from fastapi import Depends, FastAPI

from .auth import require_service_key
from .db import DB_PATH, TABLES, one
from .routers import payers, records, sessions

app = FastAPI(
    title="ClinForge Mock EHR",
    description="Synthetic data only. Not for clinical care or medical decision-making.",
    version="0.1.0",
)
for _r in (records.router, payers.router, sessions.router):
    app.include_router(_r, prefix="/api/v1", dependencies=[Depends(require_service_key)])


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "db": DB_PATH,
        "patients": one("SELECT COUNT(*) AS n FROM patients")["n"],
        "tables": sorted(TABLES),
        "notice": "Simulation data only.",
    }
