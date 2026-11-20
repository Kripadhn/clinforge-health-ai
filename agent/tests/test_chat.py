import asyncio

from agent_service.llm import LLM, Replay
from agent_service.mcp_client import ToolDenied
from agent_service.service import handle
from app.main import app
from clinical_shared.ehr import AuthError, EHRApi
from fastapi.testclient import TestClient
from mcp_clinical_server.tools import ClinicalTools

tools = ClinicalTools(EHRApi(TestClient(app), base="", key="test-key"))


class InProcessCaller:
    """Same contract as MCPCaller, but routed straight to the scope-enforcing tool layer."""

    def __init__(self, token):
        self.token = token

    async def call(self, name, **args):
        try:
            return getattr(tools, name)(self.token, **args)
        except AuthError as e:
            raise ToolDenied(str(e))


class Stub(LLM):
    def __init__(self, text):
        self.name, self.text = "stub", text

    def complete(self, system, prompt):
        return self.text


def chat(token, message, llm=None, patient_id=None):
    return asyncio.run(handle(message, patient_id, InProcessCaller(token), llm or LLM()))


def _mine(token):
    return tools.list_my_patients(token)


def test_summary_is_cited_and_disclaimed():
    r = chat("tok_adams_valid", "Summarize " + _mine("tok_adams_valid")[0]["last_name"])
    assert r["patient_id"] == _mine("tok_adams_valid")[0]["id"] and r["model"] == "none"
    assert "Simulation data only" in r["answer"] and r["citations"]


def test_other_clinicians_patient_is_denied():
    theirs = _mine("tok_baker_valid")[0]["id"]
    r = chat("tok_adams_valid", "show medications", patient_id=theirs)
    assert "cannot access" in r["answer"] and not r["citations"]
    assert any(c["ok"] is False for c in r["tool_calls"])


def test_ambiguous_patient_asks_which():
    r = chat("tok_adams_valid", "show medications")
    assert r["patient_id"] is None and "Which patient" in r["answer"]


def test_intents_route_to_expected_tools():
    p = _mine("tok_adams_valid")[0]
    for text, tool in (("medications for " + p["last_name"], "list_medications"),
                       ("claims for " + p["last_name"], "list_claims"),
                       ("insurance coverage for " + p["last_name"], "get_patient_coverage")):
        assert tool in [c["tool"] for c in chat("tok_adams_valid", text)["tool_calls"]]


def test_llm_output_needs_valid_citations():
    p = _mine("tok_adams_valid")[0]
    bad = chat("tok_adams_valid", "summary " + p["last_name"], Stub("All good [cond:99999999]"))
    assert bad["model"] == "none"
    rid = chat("tok_adams_valid", "summary " + p["last_name"])["citations"][0]
    good = chat("tok_adams_valid", "summary " + p["last_name"], Stub("Record [%s]." % rid))
    assert good["model"] == "stub"


def test_replay_without_fixture_falls_back(tmp_path):
    p = _mine("tok_adams_valid")[0]
    r = chat("tok_adams_valid", "summary " + p["last_name"], Replay(str(tmp_path / "x.json")))
    assert r["model"] == "none"


def test_views_endpoints_require_auth():
    from agent_service.main import app as agent_app
    c = TestClient(agent_app)
    assert c.get("/views/patients").status_code == 401
    assert c.get("/views/lab-trend?patient_id=x&q=a1c").status_code == 401
    assert c.get("/views/timeline?patient_id=x").status_code == 401
