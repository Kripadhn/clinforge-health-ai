"""Compute eval ground truth from clinical.db -> data/ground_truth.json (independent of the agent code path)."""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPEN = "(stop_at IS NULL OR LENGTH(stop_at) = 0)"


def main() -> None:
    db = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data" / "clinical.db")
    out = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "data" / "ground_truth.json")
    con = sqlite3.connect(db)
    truth = {}
    tokens = [r[0] for r in con.execute("SELECT token FROM care_sessions WHERE expires_at > ? ORDER BY token",
                                         ("2026-01-01",))]
    for tok in tokens:
        pts = []
        for pid, fn, ln in con.execute(
                "SELECT p.id, p.first_name, p.last_name FROM care_session_patients s "
                "JOIN patients p ON p.id = s.patient_id WHERE s.token = ? ORDER BY p.last_name", (tok,)):
            q = lambda sql: [r[0] for r in con.execute(sql, (pid,))]  # noqa: E731
            pts.append({
                "id": pid, "first_name": fn, "last_name": ln,
                "last_name_clean": "".join(c for c in ln if not c.isdigit()),
                "med_names": q("SELECT description FROM medications WHERE patient_id=? AND %s ORDER BY start_at DESC" % OPEN),
                "condition_names": q("SELECT description FROM conditions WHERE patient_id=? AND %s ORDER BY start_at DESC" % OPEN),
                "med_keywords": [next((w for w in n.split() if w.isalpha() and len(w) >= 4), n)
                                 for n in q("SELECT description FROM medications WHERE patient_id=? AND %s ORDER BY start_at DESC" % OPEN)],
                "claim_count": q("SELECT COUNT(*) FROM claims WHERE patient_id=?")[0],
                "a1c_count": con.execute(
                    "SELECT COUNT(*) FROM observations WHERE patient_id=? AND description LIKE ?",
                    (pid, "%A1c%")).fetchone()[0],
                "payer_names": q("SELECT p.name FROM payer_transitions t JOIN payers p ON p.id=t.payer_id "
                                 "WHERE t.patient_id=? ORDER BY t.start_year"),
            })
        truth[tok] = pts
    Path(out).write_text(json.dumps(truth, indent=2), encoding="utf-8")
    print("wrote %s (%d clinicians)" % (out, len(truth)))


if __name__ == "__main__":
    main()
