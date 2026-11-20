import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402

client = TestClient(app, headers={"X-Service-Key": "test-key"})


def _pid():
    return client.get("/api/v1/patients?limit=1").json()[0]["id"]


def test_health():
    assert client.get("/health").json()["patients"] > 0


def test_summary_and_lists():
    pid = _pid()
    s = client.get("/api/v1/patients/%s/summary" % pid).json()
    assert s["patient"]["id"] == pid
    for t in ("conditions", "medications", "observations", "claims"):
        assert client.get("/api/v1/patients/%s/%s" % (pid, t)).status_code == 200


def test_active_filter():
    pid = _pid()
    rows = client.get("/api/v1/patients/%s/medications?active=true" % pid).json()
    assert all(not r["stop_at"] for r in rows)


def test_404_and_bad_filter():
    assert client.get("/api/v1/patients/nope").status_code == 404
    pid = _pid()
    assert client.get("/api/v1/patients/%s/conditions?extra=bogus=1" % pid).status_code == 400


def test_db_is_read_only():
    from app.db import connect
    with pytest.raises(sqlite3.OperationalError):
        connect().execute("DELETE FROM patients")


def test_payers_and_coverage():
    payers = client.get("/api/v1/payers").json()
    assert len(payers) == 10
    mapped = [p for p in payers if p["company_id"]]
    assert len(mapped) == 9
    detail = client.get("/api/v1/payers/%s" % mapped[0]["id"]).json()
    assert detail["insurer"] and detail["plans"]
    cov = client.get("/api/v1/patients/%s/coverage" % _pid()).json()
    assert "history" in cov
    assert client.get("/api/v1/payers/nope").status_code == 404


def test_requires_service_key():
    assert TestClient(app).get("/api/v1/patients").status_code == 401
    assert TestClient(app).get("/health").status_code == 200


def test_session_introspection():
    ok = client.get("/api/v1/sessions/introspect?token=tok_adams_valid").json()
    assert ok["role"] == "physician" and len(ok["patient_ids"]) == 3
    other = client.get("/api/v1/sessions/introspect?token=tok_baker_valid").json()
    assert not set(ok["patient_ids"]) & set(other["patient_ids"])
    assert client.get("/api/v1/sessions/introspect?token=tok_adams_expired").status_code == 401
    assert client.get("/api/v1/sessions/introspect?token=bogus").status_code == 401
