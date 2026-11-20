"""Read-only SQLite access and the table registry for the mock EHR."""
import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("CLINFORGE_DB", "data/clinical.db")

# table -> (default sort column, extra filterable columns)
TABLES = {
    "encounters": ("start_at", ["encounter_class", "code", "provider_id", "organization_id"]),
    "conditions": ("start_at", ["code", "encounter_id"]),
    "allergies": ("start_at", ["code"]),
    "medications": ("start_at", ["code", "encounter_id"]),
    "observations": ("observed_at", ["code", "encounter_id", "observation_type"]),
    "procedures": ("performed_at", ["code", "encounter_id"]),
    "immunizations": ("administered_at", ["code"]),
    "careplans": ("start_at", ["code", "encounter_id"]),
    "claims": ("service_start_at", ["claim_status", "claim_type", "payer_id"]),
}
HAS_STOP = ("conditions", "medications", "careplans", "allergies", "encounters")


def connect() -> sqlite3.Connection:
    """Open the database strictly read-only (mode=ro + query_only)."""
    path = os.path.abspath(DB_PATH).replace("\\", "/")
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only = ON")
    return con


def query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    con = connect()
    try:
        return [dict(r) for r in con.execute(sql, params)]
    finally:
        con.close()


def one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    rows = query(sql, params)
    return rows[0] if rows else None
