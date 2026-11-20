"""Replace placeholder payers with Synthea's payers.csv, fill payer_crosswalk by
exact name match against insurance_companies, and load payer_transitions
(patient coverage history) for patients present in the DB. Idempotent.

Usage: python scripts/link_payers.py --csv-dir <synthea csv folder> [--db data/clinical.db]
"""
import argparse
import csv
import os
import sqlite3


def _f(v):
    return float(v) if v not in (None, "") else None


def _i(v):
    return int(float(v)) if v not in (None, "") else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/clinical.db")
    ap.add_argument("--csv-dir", required=True)
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.execute("PRAGMA foreign_keys = ON")

    with open(os.path.join(a.csv_dir, "payers.csv"), newline="", encoding="utf-8-sig") as f:
        payers = list(csv.DictReader(f))
    con.execute("DROP TABLE IF EXISTS payers")
    con.execute(
        """CREATE TABLE payers (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, address TEXT, city TEXT, state TEXT, zip TEXT,
        phone TEXT, amount_covered REAL, amount_uncovered REAL, revenue REAL,
        covered_encounters INTEGER, uncovered_encounters INTEGER, unique_customers INTEGER,
        qols_avg REAL, member_months INTEGER, source_system TEXT)""")
    con.executemany(
        "INSERT INTO payers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(r["Id"], r["NAME"], r["ADDRESS"], r["CITY"], r["STATE_HEADQUARTERED"], r["ZIP"], r["PHONE"],
          _f(r["AMOUNT_COVERED"]), _f(r["AMOUNT_UNCOVERED"]), _f(r["REVENUE"]),
          _i(r["COVERED_ENCOUNTERS"]), _i(r["UNCOVERED_ENCOUNTERS"]), _i(r["UNIQUE_CUSTOMERS"]),
          _f(r["QOLS_AVG"]), _i(r["MEMBER_MONTHS"]), "synthea") for r in payers])

    # crosswalk: exact (case-insensitive) name match; no match stays NULL
    con.execute("DELETE FROM payer_crosswalk")
    ids = {n.lower(): i for i, n in con.execute("SELECT id, name FROM insurance_companies")}
    unmatched = []
    for r in payers:
        cid = ids.get(r["NAME"].lower())
        if cid is None:
            unmatched.append(r["NAME"])
        con.execute("INSERT INTO payer_crosswalk VALUES (?,?,?)",
                    (r["Id"], cid, "name match" if cid else "no insurer master entry"))

    con.execute("DROP TABLE IF EXISTS payer_transitions")
    con.execute(
        """CREATE TABLE payer_transitions (
        patient_id TEXT NOT NULL REFERENCES patients(id), start_year INTEGER, end_year INTEGER,
        payer_id TEXT NOT NULL REFERENCES payers(id), ownership TEXT, source_system TEXT)""")
    pts = {r[0] for r in con.execute("SELECT id FROM patients")}
    with open(os.path.join(a.csv_dir, "payer_transitions.csv"), newline="", encoding="utf-8-sig") as f:
        rows = [(r["PATIENT"], _i(r["START_YEAR"]), _i(r["END_YEAR"]), r["PAYER"], r["OWNERSHIP"], "synthea")
                for r in csv.DictReader(f) if r["PATIENT"] in pts]
    con.executemany("INSERT INTO payer_transitions VALUES (?,?,?,?,?,?)", rows)
    con.execute("CREATE INDEX idx_transitions_patient ON payer_transitions(patient_id, start_year)")
    con.commit()
    print("payers=%d unmatched=%s transitions=%d fk_violations=%d" % (
        len(payers), unmatched, len(rows), len(con.execute("PRAGMA foreign_key_check").fetchall())))


if __name__ == "__main__":
    main()
