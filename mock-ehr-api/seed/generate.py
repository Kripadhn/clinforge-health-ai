"""Seed orchestrator: applies payer/insurance/session tables to data/clinical.db.

Usage: python seed/generate.py --csv-dir <synthea csv dir> --companies <csv> --plans <csv>
The base patient/encounter tables come from the Synthea importer (already in clinical.db).
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def run(script: str, *args: str) -> None:
    subprocess.run([sys.executable, str(HERE / script), *args], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(HERE.parent.parent / "data" / "clinical.db"))
    ap.add_argument("--csv-dir", required=True)
    ap.add_argument("--companies", required=True)
    ap.add_argument("--plans", required=True)
    a = ap.parse_args()
    # insurer tables first; link_payers then fills payers, crosswalk and transitions
    run("load_insurance.py", "--db", a.db, "--companies", a.companies, "--plans", a.plans)
    run("link_payers.py", "--db", a.db, "--csv-dir", a.csv_dir)
    run("make_sessions.py", "--db", a.db)
    run("add_trap.py", "--db", a.db)


if __name__ == "__main__":
    main()
