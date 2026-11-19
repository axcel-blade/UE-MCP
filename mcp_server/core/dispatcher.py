"""Dispatch MCP tool calls to the Unreal bridge."""

from __future__ import annotations

import logging
from typing import Any

from mcp_server.config import Settings
from mcp_server.core.job_manager import JobManager
from mcp_server.core.permissions import assert_tool_allowed
from mcp_server.core.response import fail, ok
from mcp_server.exceptions import UnrealEngineMCPError

logger = logging.getLogger(__name__)


def flatten_tool_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize tool args from hosts that wrap payloads as {"params": {...}}.

    FastMCP tools often use ``**params``, so a Cursor-style ``{"params": {...}}``
    request becomes nested again before it reaches the bridge. Flatten one level.
    """
    out = dict(params or {})
    if "params" in out and isinstance(out["params"], dict):
        nested = out.pop("params")
        out = {**nested, **out}
    return out


class Dispatcher:
    def __init__(self, settings: Settings, client: Any, jobs: JobManager) -> None:
        self.settings = settings
        self.client = client
        self.jobs = jobs

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        params = flatten_tool_params(params)
        confirmed = bool(params.pop("confirmed", confirmed))
        try:
            assert_tool_allowed(self.settings, method, confirmed=confirmed)
            response = await self.client.request(method, params)
            if not response.ok:
                err = response.error
                return fail(
                    err.message if err else "Unknown engine error",
                    code=err.code if err else "engine_error",
                    details=err.details if err else {},
                )
            result = response.result or {}
            if response.async_job_id:
                result = {**result, "async_job_id": response.async_job_id}
            return ok(result, duration_ms=response.duration_ms)
        except UnrealEngineMCPError as exc:
            logger.warning("Tool %s failed: %s", method, exc.message)
            return fail(exc.message, code=exc.code)
        except Exception as exc:
            logger.exception("Unexpected error in %s", method)
            return fail(str(exc), code="unexpected_error")
