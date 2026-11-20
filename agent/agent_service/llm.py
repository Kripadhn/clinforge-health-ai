"""LLM providers selected by LLM_PROVIDER: ollama (default), none (deterministic), replay (CI)."""
import hashlib
import json
import os
import re
from typing import Optional

import httpx
from clinical_shared.config import LLM_PROVIDER, env


class LLM:
    name = "none"

    def complete(self, system: str, prompt: str) -> Optional[str]:
        return None  # no-LLM: callers use their deterministic template


class Ollama(LLM):
    def __init__(self) -> None:
        self.model = env("OLLAMA_MODEL", "qwen3:8b")
        self.host = env("OLLAMA_HOST", "http://localhost:11434")
        self.name = "ollama:" + self.model

    def complete(self, system: str, prompt: str) -> Optional[str]:
        r = httpx.post(self.host + "/api/chat", timeout=300, json={
            "model": self.model, "stream": False, "think": False, "options": {"temperature": 0, "seed": 7},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
        r.raise_for_status()
        text = r.json()["message"]["content"]
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()  # qwen3 reasoning block


def _key(system: str, prompt: str) -> str:
    return hashlib.sha256((system + "|||" + prompt).encode("utf-8")).hexdigest()


class Replay(LLM):
    """Deterministic CI mode: recorded responses keyed by prompt hash; wraps a live LLM to record."""
    name = "replay"

    def __init__(self, path: Optional[str] = None, live: Optional[LLM] = None) -> None:
        self.path = path or env("LLM_REPLAY_FILE", "eval/fixtures/llm_replay.json")
        self.live = live
        self.data = {}  # type: Dict[str, str]
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                self.data = json.load(f)

    def complete(self, system: str, prompt: str) -> Optional[str]:
        k = _key(system, prompt)
        if k not in self.data:
            if self.live is None:
                return None  # unknown prompt: fall back to the template instead of failing CI
            self.data[k] = self.live.complete(system, prompt)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        return self.data[k]


def get_llm(provider: Optional[str] = None) -> LLM:
    p = provider or LLM_PROVIDER()
    if p == "none":
        return LLM()
    if p == "ollama":
        return Ollama()
    if p == "replay":
        # LLM_RECORD=1 wraps live Ollama so missing prompts are recorded into the fixture file
        return Replay(live=Ollama() if env("LLM_RECORD", "0") == "1" else None)
    raise ValueError("unknown LLM_PROVIDER: " + p)
