"""Load insurer master + plan tables into clinical.db (idempotent).

Usage: python scripts/load_insurance.py --companies insurance_companies.csv --plans insurance_plans.csv [--db data/clinical.db]

Creates insurance_companies, insurance_plans and payer_crosswalk. The crosswalk
links the UUID payer_ids used by encounters/claims/medications to insurer ids;
it is filled by link_payers.py.
"""
import argparse
import csv
import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS insurance_companies (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, address TEXT, city TEXT, state_hq TEXT,
        zip TEXT, phone TEXT, states_covered TEXT, ownership TEXT, source_system TEXT)""",
    """CREATE TABLE IF NOT EXISTS insurance_plans (
        plan_id TEXT PRIMARY KEY, payer_id TEXT NOT NULL REFERENCES insurance_companies(id),
        name TEXT NOT NULL, services_covered TEXT, deductible REAL, default_coinsurance REAL,
        default_copay REAL, monthly_premium REAL, max_out_of_pocket REAL,
        medicare_supplement INTEGER, is_aca_plan INTEGER, income_based_premium INTEGER,
        eligibility_policy TEXT, start_year INTEGER, end_year INTEGER, priority_level INTEGER,
        notes TEXT, source_system TEXT)""",
    """CREATE TABLE IF NOT EXISTS payer_crosswalk (
        payer_id TEXT PRIMARY KEY, company_id TEXT REFERENCES insurance_companies(id), note TEXT)""",
    "CREATE INDEX IF NOT EXISTS idx_plans_payer ON insurance_plans(payer_id)",
]


def _num(v):
    return float(v) if v not in (None, "") else None


def _int(v):
    return int(float(v)) if v not in (None, "") else None


def _bool(v):
    return 1 if str(v).strip().lower() == "true" else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/clinical.db")
    ap.add_argument("--companies", required=True)
    ap.add_argument("--plans", required=True)
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.execute("PRAGMA foreign_keys = ON")
    for stmt in SCHEMA:
        con.execute(stmt)

    with open(a.companies, newline="", encoding="utf-8-sig") as f:
        companies = []
        for r in csv.DictReader(f):
            z = (r["Zip"] or "").strip()
            companies.append((
                r["Id"], r["Name"], r["Address"], r["City"], r["State Headquarterd"],
                z.zfill(5) if z.isdigit() else z,  # CSV dropped leading zeros (CT zips)
                r["Phone"], r["States Covered"], r["Ownership"], "insurance_csv"))
    with open(a.plans, newline="", encoding="utf-8-sig") as f:
        plans = [(
            r["Plan Id"], r["Payer Id"], r["Name"], r["Services Covered"], _num(r["Deductible"]),
            _num(r["Default Coinsurance"]), _num(r["Default Copay"]), _num(r["Monthly Premium"]),
            _num(r["Max Out of Pocket"]), _bool(r["Medicare Supplement"]), _bool(r["Is ACA Plan"]),
            _bool(r["Income Based Premium"]), r["Eligibility Policy"], _int(r["Start Year"]),
            _int(r["End Year"]), _int(r["Priority Level"]), r["Notes"] or None, "insurance_csv")
            for r in csv.DictReader(f)]

    con.executemany("INSERT OR REPLACE INTO insurance_companies VALUES (?,?,?,?,?,?,?,?,?,?)", companies)
    con.executemany("INSERT OR REPLACE INTO insurance_plans VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", plans)
    con.execute(
        "INSERT INTO audit_events(occurred_at, event_type, actor, detail_json) VALUES (?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), "import.insurance", "load_insurance.py",
         json.dumps({"companies": len(companies), "plans": len(plans)})))
    con.commit()
    bad = con.execute("PRAGMA foreign_key_check").fetchall()
    print("companies=%d plans=%d fk_violations=%d" % (len(companies), len(plans), len(bad)))


if __name__ == "__main__":
    main()
