"""Environment-driven settings (see .env.example)."""
import os

DISCLAIMER = "Simulation data only. Not for clinical care or medical decision-making."


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


EHR_API_URL = lambda: env("EHR_API_URL", "http://localhost:8001")  # noqa: E731
EHR_SERVICE_KEY = lambda: env("EHR_SERVICE_KEY", "dev-service-key")  # noqa: E731
MCP_URL = lambda: env("MCP_URL", "http://localhost:8002/mcp")  # noqa: E731
LLM_PROVIDER = lambda: env("LLM_PROVIDER", "ollama")  # noqa: E731  (ollama | none | replay)
