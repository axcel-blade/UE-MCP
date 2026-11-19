"""FastMCP server factory."""

from __future__ import annotations

from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from mcp_server import __version__
from mcp_server.clients.connection_manager import ConnectionManager
from mcp_server.clients.unreal_client import UnrealClient
from mcp_server.config import Settings, load_settings
from mcp_server.core.dispatcher import Dispatcher
from mcp_server.core.job_manager import JobManager
from mcp_server.logger import setup_logging
from mcp_server.prompts.registry import register_prompts
from mcp_server.resources.registry import register_resources
from mcp_server.tools import register_all_tools

INSTRUCTIONS = """
You are connected to Unreal Engine 5 through UnrealEngineMCP.

Required workflow for scene edits:
1. Inspect the current level and actors before changing content.
2. Prefer dedicated tools over arbitrary Python/console execution.
3. Make changes with clear actor/asset names.
4. Validate results (transforms, compilation, references).
5. Capture a screenshot when visual verification matters.
6. Report concrete engine results, never invent success.

Safe mode restricts destructive and script-execution tools.
All engine operations run inside the Unreal Editor via the UnrealEngineMCP plugin.
""".strip()


@dataclass
class AppContext:
    settings: Settings
    connections: ConnectionManager
    client: UnrealClient
    dispatcher: Dispatcher
    jobs: JobManager


def create_server(settings: Settings | None = None) -> FastMCP:
    settings = settings or load_settings()
    setup_logging(settings.server.log_level, settings.server.log_file)

    connections = ConnectionManager(settings)
    client = UnrealClient(connections)
    jobs = JobManager()
    dispatcher = Dispatcher(settings, client, jobs)
    ctx = AppContext(
        settings=settings,
        connections=connections,
        client=client,
        dispatcher=dispatcher,
        jobs=jobs,
    )

    mcp = FastMCP(name=settings.server.name, instructions=INSTRUCTIONS)
    register_all_tools(mcp, ctx)
    register_resources(mcp, ctx)
    register_prompts(mcp)

    @mcp.tool(name="unreal_engine_mcp_version")
    async def unreal_engine_mcp_version() -> dict:
        """Return UnrealEngineMCP server version and non-secret configuration."""
        return {
            "success": True,
            "result": {
                "version": __version__,
                "host": settings.host,
                "port": settings.port,
                "security_mode": settings.security.mode,
                "protocol_version": settings.unreal.protocol_version,
                "auth_configured": bool(settings.unreal.auth_token),
            },
        }

    @mcp.tool(name="unreal_job_status")
    async def unreal_job_status(job_id: str) -> dict:
        """Get status for an asynchronous Unreal job."""
        job = jobs.get(job_id)
        if not job:
            return {
                "success": False,
                "error": {"code": "not_found", "message": f"Unknown job {job_id}"},
            }
        return {"success": True, "result": jobs.to_dict(job)}

    return mcp
