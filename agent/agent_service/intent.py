"""Deterministic intent detection and patient/lab-term resolution."""
import re
from typing import Any, Dict, List, Optional

STOP = set("the a an of for on in to is are what whats show me give tell about trend trends level levels "
           "result results lab labs value values history over time patient please and with her his their "
           "latest recent last how has have does did when was were my".split())
INTENTS = [
    ("claims", r"\bclaims?\b|billing|billed"),
    ("coverage", r"coverage|insur|payer"),
    ("medications", r"medicat|\bmeds?\b|drugs?\b|prescri"),
    ("careplans", r"care ?plans?"),
    ("conditions", r"condition|diagnos|problem list|problems"),
    ("labs", r"\blabs?\b|trend|a1c|glucose|cholesterol|creatinine|hemoglobin|blood pressure|bmi|weight|level"),
]


def _clean(name: str) -> str:
    return re.sub(r"\d+", "", name).lower()  # Synthea appends digits to names


def detect_intent(message: str) -> str:
    low = message.lower()
    for name, pat in INTENTS:
        if re.search(pat, low):
            return name
    return "summary"


def resolve_patient(message: str, patients: List[Dict[str, Any]], explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit
    low = message.lower()
    hits = [p["id"] for p in patients if any(_clean(p[k]) in low for k in ("first_name", "last_name"))]
    if len(hits) == 1:
        return hits[0]
    return patients[0]["id"] if len(patients) == 1 else None


def lab_terms(message: str, patients: List[Dict[str, Any]]) -> List[str]:
    names = {_clean(n) for p in patients for n in (p["first_name"], p["last_name"])}
    words = [w for w in re.findall(r"[a-zA-Z0-9]+", message) if w.lower() not in STOP and _clean(w) not in names]
    return ([" ".join(words)] if len(words) > 1 else []) + words
