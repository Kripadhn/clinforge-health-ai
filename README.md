# ClinForge Health AI

A locally deployable agentic clinical simulation, structured like Finpilot-AI: host -> agent -> MCP server -> mock EHR API -> SQLite.
Synthetic patients, encounters, conditions, medications, lab observations, procedures, care plans, claims and payer coverage.

**Synthetic data only. Not for clinical care or medical decision-making.**

## Layout
| dir | purpose |
|---|---|
| `mock-ehr-api` | FastAPI read-only EHR (port 8001): `app`, `seed`, `tests` |
| `mcp-server` | MCP server, Streamable HTTP `/mcp` (port 8002), patient-scope enforcement |
| `agent` | `POST /chat` (port 8003); Ollama, none, or replay LLM modes |
| `host` | chat UI (port 5173); `/views.html` lab-trend + encounter-timeline views |
| `shared` | `clinical_shared`: EHR client, config, citation policy |
| `apps` | clinical views (lab trend, encounter timeline) served by the host |
| `eval` | case schema, public and candidate cases, harness |
| `scripts` | `compute_truth.py`, `ci_eval.sh`, `check_spec_first.sh` |
| `data` | `clinical.db`, `ground_truth.json` |

## Run (Docker)
```
ollama pull qwen3:8b
make seed truth
make up            # open http://localhost:5173
```

## Run (without Docker, no make)
See `docs/RUNNING.md`.

## Test tokens
`tok_adams_valid`, `tok_baker_valid`, `tok_clark_valid`, `tok_adams_expired`. Each valid token sees only its own three patients.

## Evaluate
`make eval CASES=eval/cases/public` or `eval/cases/candidate`. Reports go to `reports/`.
Isolation and injection-resistance must be 100 percent.

## Data
`data/clinical.db` is a Synthea CSV import plus `payers`, `payer_crosswalk`, `insurance_companies`, `insurance_plans`,
`payer_transitions`, `care_sessions`. Rebuild the derived tables with `mock-ehr-api/seed/generate.py`.
