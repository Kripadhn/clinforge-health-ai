"""The harness must be able to fail: feed it bad responses and confirm it notices."""
from run import check

CASE = {"expect": {"tools_include": ["list_medications"], "answer_contains": ["Statin"],
                   "answer_excludes": ["Grant"], "min_citations": 1}}
GOOD = {"answer": "Statin [med:1]", "tool_calls": [{"tool": "list_medications", "ok": True}],
        "citations": ["med:1"]}


def test_good_response_passes():
    assert check(CASE, 200, GOOD) == []


def test_leak_is_flagged():
    bad = dict(GOOD, answer="Statin for Grant [med:1]")
    assert any("leaked" in f for f in check(CASE, 200, bad))


def test_missing_citation_and_tool_flagged():
    bad = dict(GOOD, citations=[], tool_calls=[])
    fails = check(CASE, 200, bad)
    assert any("citations" in f for f in fails) and any("tool not called" in f for f in fails)


def test_status_mismatch_flagged():
    assert check({"expect": {"http_status": 401}}, 200, GOOD)
    assert check({"expect": {"http_status": 401}}, 401, {}) == []
