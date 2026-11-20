# AI usage

This project was built with Claude Code (Claude Sonnet 5.5) as a pair-programming assistant.

- Generated: service scaffolding, seed scripts, MCP tools, agent logic, eval harness, docs.
- Verified by running: unit tests, live three-service smoke tests, both eval suites, and a real Ollama (qwen3:8b) call.
- Human decisions: domain mapping, payer crosswalk approach, data sources, scope.
- All data is synthetic (Synthea) plus user-provided insurer reference tables.
