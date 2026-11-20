#!/usr/bin/env bash
# CI eval: start the three services with LLM_PROVIDER=none, run both case folders, stop the services.
set -euo pipefail
SEP=":"; case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) SEP=";";; esac
export PYTHONPATH="shared${SEP}mock-ehr-api${SEP}mcp-server${SEP}agent" CLINFORGE_DB="${CLINFORGE_DB:-data/clinical.db}"
export EHR_SERVICE_KEY=dev-service-key EHR_API_URL=http://localhost:8001 MCP_URL=http://localhost:8002/mcp LLM_PROVIDER=none
PY="${PY:-python}"
$PY scripts/compute_truth.py
$PY -m uvicorn app.main:app --port 8001 & P1=$!
$PY -m mcp_clinical_server.server & P2=$!
$PY -m uvicorn agent_service.main:app --port 8003 & P3=$!
trap 'kill $P1 $P2 $P3 2>/dev/null || true' EXIT
for i in $(seq 1 30); do curl -sf localhost:8003/health >/dev/null && break; sleep 1; done
$PY eval/harness/run.py --cases eval/cases/public
$PY eval/harness/run.py --cases eval/cases/candidate
