"""Calls MCP tools over Streamable HTTP, forwarding the user bearer token."""
import json
from typing import Any

from clinical_shared.config import MCP_URL
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class ToolDenied(Exception):
    """The MCP server refused or failed a tool call."""


class MCPCaller:
    def __init__(self, token: str, url: str = "") -> None:
        self.token, self.url = token, url or MCP_URL()

    async def call_many(self, calls):
        """Run several (name, args) calls in one MCP session. Returns a list of parsed results or ToolDenied."""
        out = []
        async with streamablehttp_client(self.url, headers={"Authorization": "Bearer " + self.token}) as (r, w, _):
            async with ClientSession(r, w) as session:
                await session.initialize()
                for name, args in calls:
                    res = await session.call_tool(name, args)
                    text = "".join(getattr(c, "text", "") for c in res.content)
                    out.append(ToolDenied(text) if res.isError else json.loads(text))
        return out

    async def call(self, name: str, **args: Any) -> Any:
        res = (await self.call_many([(name, args)]))[0]
        if isinstance(res, ToolDenied):
            raise res
        return res
