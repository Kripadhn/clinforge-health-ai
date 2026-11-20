# Architecture

```
host :5173  ->  agent :8003  ->  MCP server :8002  ->  mock-ehr-api :8001  ->  data/clinical.db (read-only)
                    |
                    +-> Ollama :11434 (optional; LLM_PROVIDER=none uses the deterministic router)
```

## Mapping from Finpilot-AI
| Finpilot-AI | ClinForge |
|---|---|
| mock-bank-api, bank.db | mock-ehr-api, clinical.db (Synthea import plus payer and session tables) |
| mcp-server/mcp_bank_server | mcp-server/mcp_clinical_server |
| shared/bank_shared | shared/clinical_shared |
| customer token (tok_aisha_valid) | care-team token (tok_adams_valid) |
| customer isolation | patient-scope isolation |
| ground_truth.json | data/ground_truth.json |

## ADRs
1. **Isolation lives in the MCP server.** The EHR API is a trusted back-office service that would return any patient. The MCP server resolves the token via `/sessions/introspect` and checks the patient on every call, including encounter lookups.
2. **Deterministic first, LLM second.** The agent gathers facts with fixed rules and renders a template. The LLM only narrates, and its output is accepted only if every citation matches a retrieved record.
3. **Table-qualified citations.** Synthea-imported ids are integers unique per table, so citations are `[cond:560]`, `[med:586]`.
4. **Read-only by construction.** SQLite opened with `mode=ro` and `query_only`, compose mounts `data` read-only, and no tool writes.
5. **Payer data.** `payers` holds the Synthea payer UUIDs; `payer_crosswalk` links them to `insurance_companies` and `insurance_plans` by exact name. `NO_INSURANCE` has no insurer entry by design.

## Known limits
- Intent routing is keyword-based; free-form multi-intent questions fall back to a chart summary.
- Sessions are seeded static tokens, not a real identity provider.
- A local qwen3:8b call takes tens of seconds; CI uses `LLM_PROVIDER=none`.
- No OpenTelemetry yet.
