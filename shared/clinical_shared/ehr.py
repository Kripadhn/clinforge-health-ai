"""Client for the mock EHR API. Accepts an httpx-compatible client so tests can use TestClient."""
from typing import Any, Dict, Optional

import httpx

from .config import EHR_API_URL, EHR_SERVICE_KEY

PREFIX = "/api/v1"


class AuthError(Exception):
    """Token unknown, expired, or not permitted for the requested record."""


class EHRApi:
    def __init__(self, http: Optional[Any] = None, base: Optional[str] = None, key: Optional[str] = None) -> None:
        self.http = http or httpx.Client(timeout=20)
        self.base = EHR_API_URL() if base is None else base
        self.key = key or EHR_SERVICE_KEY()

    def get(self, path: str, **params: Any) -> Any:
        params = {k: v for k, v in params.items() if v is not None}
        r = self.http.get(self.base + PREFIX + path, params=params, headers={"X-Service-Key": self.key})
        r.raise_for_status()
        return r.json()

    def introspect(self, token: str) -> Dict[str, Any]:
        r = self.http.get(self.base + PREFIX + "/sessions/introspect", params={"token": token},
                          headers={"X-Service-Key": self.key})
        if r.status_code == 401:
            raise AuthError(r.json().get("detail", "unauthorized"))
        r.raise_for_status()
        return r.json()
