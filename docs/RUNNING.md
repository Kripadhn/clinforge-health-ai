# Running without make (Windows, Git Bash)

```
python -m venv .venv
.venv/Scripts/python -m pip install fastapi uvicorn httpx pydantic "mcp<2" pytest pytest-asyncio
export PYTHONPATH="shared;mock-ehr-api;mcp-server;agent"
export CLINFORGE_DB=data/clinical.db EHR_API_URL=http://localhost:8001 MCP_URL=http://localhost:8002/mcp LLM_PROVIDER=none
.venv/Scripts/python mock-ehr-api/seed/make_sessions.py --db data/clinical.db
.venv/Scripts/python scripts/compute_truth.py
```
Then, in separate terminals (same exports):
```
.venv/Scripts/python -m uvicorn app.main:app --port 8001
.venv/Scripts/python -m mcp_clinical_server.server
.venv/Scripts/python -m uvicorn agent_service.main:app --port 8003
node host/server.mjs
```
Use `LLM_PROVIDER=ollama` for the local model (qwen3:8b). Tests: `EHR_SERVICE_KEY=test-key .venv/Scripts/python -m pytest -q`.
Use `;` as the PYTHONPATH separator on Windows and `:` on Linux or macOS.
