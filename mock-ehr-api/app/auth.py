"""Service-key auth. The API is a trusted back-office service: callers must send X-Service-Key."""
import os

from fastapi import Header, HTTPException


def require_service_key(x_service_key: str = Header(None)) -> None:
    expected = os.environ.get("EHR_SERVICE_KEY", "dev-service-key")
    if x_service_key != expected:
        raise HTTPException(401, "missing or invalid X-Service-Key")
