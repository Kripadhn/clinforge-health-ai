"""Turns an intent into MCP tool calls and a list of cited facts (id, text, date)."""
from typing import Any, Dict

from .intent import lab_terms
from .mcp_client import ToolDenied


def _fact(prefix: str, rec: Dict[str, Any], text: str, date: str = "") -> Dict[str, str]:
    return {"id": "%s:%s" % (prefix, rec["id"]), "text": text, "date": (date or "")[:10]}


def _rows(prefix, rows, suffix=""):
    return [_fact(prefix, r, r["description"] + suffix, r.get("start_at", "")) for r in rows]


async def gather(caller, intent, pid, message, patients, calls):
    """Returns (title, facts). Every tool call is recorded in calls."""
    async def tool(name, **args):
        try:
            res = await caller.call(name, **args)
            calls.append({"tool": name, "args": args, "ok": True})
            return res
        except ToolDenied as e:
            calls.append({"tool": name, "args": args, "ok": False, "error": str(e)})
            raise

    if intent == "medications":
        return "Active medications", _rows("med", await tool("list_medications", patient_id=pid))
    if intent == "conditions":
        return "Active conditions", _rows("cond", await tool("list_conditions", patient_id=pid))
    if intent == "careplans":
        return "Active care plans", _rows("cp", await tool("list_careplans", patient_id=pid))
    if intent == "claims":
        rows = await tool("list_claims", patient_id=pid)
        return "Claims", [_fact("clm", r, "%s claim, billed %s, status %s" % (
            r["claim_type"], r["amount_billed"], r["claim_status"]), r["service_start_at"]) for r in rows[:15]]
    if intent == "coverage":
        cov = await tool("get_patient_coverage", patient_id=pid)
        return "Coverage history", [{"id": "cov:%s-%d" % (pid[:8], i), "text": "%s (%s-%s)" % (
            h["payer_name"], h["start_year"], h["end_year"] or "present"), "date": ""}
            for i, h in enumerate(cov["history"])]
    if intent == "labs":
        for term in lab_terms(message, patients):
            codes = await tool("find_observation_code", query=term)
            if codes:
                tr = await tool("get_lab_trend", patient_id=pid, code=codes[0]["code"])
                title = "%s trend (n=%s)" % (codes[0]["description"], tr["stats"]["n"])
                return title, [_fact("obs", r, "%s %s" % (r["value"], r["units"] or ""), r["observed_at"])
                               for r in tr["series"][-10:]]
        return "No matching lab found", []
    s = await tool("get_patient_summary", patient_id=pid)
    p = s["patient"]
    facts = _rows("cond", s["active_conditions"], " (condition)") + _rows("med", s["active_medications"], " (medication)")
    facts += [_fact("alg", r, r["description"] + " (allergy)") for r in s["allergies"]]
    facts += _rows("enc", s["recent_encounters"], " (encounter)")
    return "Chart summary for %s %s (%s, born %s)" % (
        p["first_name"], p["last_name"], p["gender"], p["birth_date"]), facts
