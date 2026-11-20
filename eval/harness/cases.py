"""Case loading, schema validation and {{truth}} template resolution."""
import json
import re
from pathlib import Path
from typing import Any, Dict, List

EVAL = Path(__file__).resolve().parent.parent
TRUTH = EVAL.parent / "data" / "ground_truth.json"
REF = re.compile(r"\{\{([^}]+)\}\}")


def load_truth() -> Dict[str, Any]:
    return json.loads(TRUTH.read_text(encoding="utf-8"))


def _resolve(ref: str, truth: Dict[str, Any]) -> str:
    cur = truth  # path like tok_adams_valid.0.med_names.0
    for part in ref.strip().split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return str(cur)


def resolve(obj: Any, truth: Dict[str, Any]) -> Any:
    if isinstance(obj, str):
        return REF.sub(lambda m: _resolve(m.group(1), truth), obj)
    if isinstance(obj, list):
        return [resolve(x, truth) for x in obj]
    if isinstance(obj, dict):
        return {k: resolve(v, truth) for k, v in obj.items()}
    return obj


def validate(case: Dict[str, Any]) -> List[str]:
    """Light schema check (required keys and types) so validate-cases has no extra dependency."""
    errs = []
    schema = json.loads((EVAL / "schema" / "case.schema.json").read_text(encoding="utf-8"))
    for k in schema["required"]:
        if k not in case:
            errs.append("missing " + k)
    for k in case:
        if k not in schema["properties"]:
            errs.append("unknown key " + k)
    for k in case.get("expect", {}):
        if k not in schema["properties"]["expect"]["properties"]:
            errs.append("unknown expect key " + k)
    return errs


def load_cases(folder: str, truth: Dict[str, Any]) -> List[Dict[str, Any]]:
    cases = []
    for f in sorted(Path(folder).glob("*.json")):
        raw = json.loads(f.read_text(encoding="utf-8"))
        for c in (raw if isinstance(raw, list) else [raw]):
            errs = validate(c)
            if errs:
                raise ValueError("%s %s: %s" % (f.name, c.get("id"), "; ".join(errs)))
            cases.append(resolve(c, truth))
    return cases
