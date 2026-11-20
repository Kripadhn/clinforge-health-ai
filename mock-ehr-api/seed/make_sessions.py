"""Seed care-team sessions (token -> clinician -> assigned patients). Deterministic, idempotent.

Usage: python seed/make_sessions.py [--db ../data/clinical.db]
Patients are ranked by record volume (then id) and dealt round-robin, so each clinician gets 3 disjoint,
data-rich patients and isolation is testable.
"""
import argparse
import sqlite3

CLINICIANS = [
    ("tok_adams_valid", "CL001", "Dr. Adams", "physician", "2099-01-01T00:00:00+00:00", 0),
    ("tok_baker_valid", "CL002", "Dr. Baker", "physician", "2099-01-01T00:00:00+00:00", 1),
    ("tok_clark_valid", "CL003", "Nurse Clark", "nurse", "2099-01-01T00:00:00+00:00", 2),
    ("tok_adams_expired", "CL001", "Dr. Adams", "physician", "2000-01-01T00:00:00+00:00", 0),
]
PER = 3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="../data/clinical.db")
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.execute("DROP TABLE IF EXISTS care_session_patients")
    con.execute("DROP TABLE IF EXISTS care_sessions")
    con.execute(
        "CREATE TABLE care_sessions (token TEXT PRIMARY KEY, clinician_id TEXT NOT NULL, name TEXT NOT NULL, "
        "role TEXT NOT NULL, expires_at TEXT NOT NULL)")
    con.execute(
        "CREATE TABLE care_session_patients (token TEXT NOT NULL REFERENCES care_sessions(token), "
        "patient_id TEXT NOT NULL REFERENCES patients(id), PRIMARY KEY (token, patient_id))")
    pids = [r[0] for r in con.execute(
        "SELECT p.id FROM patients p ORDER BY (SELECT COUNT(*) FROM observations o WHERE o.patient_id = p.id) DESC, p.id")]
    for token, cid, name, role, exp, slot in CLINICIANS:
        con.execute("INSERT INTO care_sessions VALUES (?,?,?,?,?)", (token, cid, name, role, exp))
        for pid in pids[slot::3][:PER]:
            con.execute("INSERT INTO care_session_patients VALUES (?,?)", (token, pid))
    con.commit()
    print("sessions=%d patients_per_clinician=%d" % (len(CLINICIANS), PER))


if __name__ == "__main__":
    main()
