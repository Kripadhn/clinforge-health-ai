"""Agent service: POST /chat on port 8003. Patient data is reachable only through MCP."""
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .llm import get_llm
from .mcp_client import MCPCaller, ToolDenied
from .service import handle
from .views import router as views_router

app = FastAPI(title="ClinForge Agent", version="0.1.0")
app.include_router(views_router)


class ChatRequest(BaseModel):
    message: str
    patient_id: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": get_llm().name}


@app.post("/chat")
async def chat(req: ChatRequest, authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    try:
        return await handle(req.message, req.patient_id, MCPCaller(authorization[7:].strip()), get_llm())
    except ToolDenied as e:
        raise HTTPException(401, str(e))
