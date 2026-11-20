import pytest
from app.main import app
from clinical_shared.ehr import AuthError, EHRApi
from fastapi.testclient import TestClient
from mcp_clinical_server.tools import ClinicalTools

tools = ClinicalTools(EHRApi(TestClient(app), base="", key="test-key"))


def _pids(token):
    return [p["id"] for p in tools.list_my_patients(token)]


def test_each_clinician_sees_only_their_patients():
    a, b = _pids("tok_adams_valid"), _pids("tok_baker_valid")
    assert len(a) == 3 and not set(a) & set(b)


def test_cross_patient_access_denied():
    mine, theirs = _pids("tok_adams_valid")[0], _pids("tok_baker_valid")[0]
    assert tools.get_patient_summary("tok_adams_valid", mine)["patient"]["id"] == mine
    for call in (tools.get_patient_summary, tools.list_medications, tools.list_claims,
                 tools.get_patient_coverage):
        with pytest.raises(AuthError):
            call("tok_adams_valid", theirs)


def test_encounter_scope_enforced():
    theirs = _pids("tok_baker_valid")[0]
    enc = tools.ehr.get("/patients/%s/encounters" % theirs, limit=1)[0]["id"]
    with pytest.raises(AuthError):
        tools.get_encounter("tok_adams_valid", enc)
    assert tools.get_encounter("tok_baker_valid", enc)["id"] == enc


def test_bad_tokens_rejected():
    for tok in (None, "", "bogus", "tok_adams_expired"):
        with pytest.raises(AuthError):
            tools.list_my_patients(tok)


def test_list_encounters_scoped():
    mine = _pids("tok_adams_valid")[0]
    rows = tools.list_encounters("tok_adams_valid", mine, limit=10)
    assert rows and all(r["patient_id"] == mine for r in rows)
    with pytest.raises(AuthError):
        tools.list_encounters("tok_adams_valid", _pids("tok_baker_valid")[0])
