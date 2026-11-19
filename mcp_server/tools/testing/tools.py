"""Auto-registered testing tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_execute_editor_python")
    async def unreal_execute_editor_python(**params: Any) -> dict[str, Any]:
        """Execute Unreal Editor Python (advanced mode)."""
        return await ctx.dispatcher.call("unreal_execute_editor_python", params)

    @mcp.tool(name="unreal_execute_console_command")
    async def unreal_execute_console_command(**params: Any) -> dict[str, Any]:
        """Execute an editor console command (advanced)."""
        return await ctx.dispatcher.call("unreal_execute_console_command", params)

    @mcp.tool(name="unreal_run_automation_test")
    async def unreal_run_automation_test(**params: Any) -> dict[str, Any]:
        """Run an Unreal automation test."""
        return await ctx.dispatcher.call("unreal_run_automation_test", params)

    @mcp.tool(name="unreal_get_automation_results")
    async def unreal_get_automation_results(**params: Any) -> dict[str, Any]:
        """Get automation test results."""
        return await ctx.dispatcher.call("unreal_get_automation_results", params)

    @mcp.tool(name="unreal_get_output_log")
    async def unreal_get_output_log(**params: Any) -> dict[str, Any]:
        """Get output log lines."""
        return await ctx.dispatcher.call("unreal_get_output_log", params)

    @mcp.tool(name="unreal_get_compile_errors")
    async def unreal_get_compile_errors(**params: Any) -> dict[str, Any]:
        """Get recent compile errors."""
        return await ctx.dispatcher.call("unreal_get_compile_errors", params)

    @mcp.tool(name="unreal_get_project_diagnostics")
    async def unreal_get_project_diagnostics(**params: Any) -> dict[str, Any]:
        """Run project diagnostics."""
        return await ctx.dispatcher.call("unreal_get_project_diagnostics", params)

    @mcp.tool(name="unreal_validate_assets")
    async def unreal_validate_assets(**params: Any) -> dict[str, Any]:
        """Validate assets."""
        return await ctx.dispatcher.call("unreal_validate_assets", params)

    @mcp.tool(name="unreal_validate_blueprints")
    async def unreal_validate_blueprints(**params: Any) -> dict[str, Any]:
        """Validate Blueprints."""
        return await ctx.dispatcher.call("unreal_validate_blueprints", params)

    @mcp.tool(name="unreal_save_all")
    async def unreal_save_all(**params: Any) -> dict[str, Any]:
        """Save dirty packages."""
        return await ctx.dispatcher.call("unreal_save_all", params)

    @mcp.tool(name="unreal_run_build")
    async def unreal_run_build(**params: Any) -> dict[str, Any]:
        """Trigger a build/cook workflow where supported."""
        return await ctx.dispatcher.call("unreal_run_build", params)
