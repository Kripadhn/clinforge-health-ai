# Targets mirror Finpilot-AI. On Windows without make, run the commands directly (see docs/RUNNING.md).
PY ?= .venv/Scripts/python
export PYTHONPATH := shared:mock-ehr-api:mcp-server:agent
export CLINFORGE_DB ?= data/clinical.db
CASES ?= eval/cases/public

setup:
	python -m venv .venv && $(PY) -m pip install fastapi uvicorn httpx pydantic "mcp<2" pytest pytest-asyncio ruff
seed:
	$(PY) mock-ehr-api/seed/make_sessions.py --db data/clinical.db
truth:
	$(PY) scripts/compute_truth.py
api:
	$(PY) -m uvicorn app.main:app --port 8001
mcp:
	$(PY) -m mcp_clinical_server.server
agent:
	$(PY) -m uvicorn agent_service.main:app --port 8003
host:
	node host/server.mjs
up:
	docker compose up --build -d
down:
	docker compose down
test:
	EHR_SERVICE_KEY=test-key $(PY) -m pytest -q
lint:
	$(PY) -m ruff check .
eval:
	$(PY) eval/harness/run.py --cases $(CASES)
validate-cases:
	$(PY) eval/harness/run.py --cases $(CASES) --validate-only
check-spec:
	bash scripts/check_spec_first.sh
.PHONY: setup seed truth api mcp agent host up down test lint eval validate-cases check-spec
