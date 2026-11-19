"""Auto-registered system tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_ping")
    async def unreal_ping(**params: Any) -> dict[str, Any]:
        """Ping the Unreal Editor bridge."""
        return await ctx.dispatcher.call("unreal_ping", params)

    @mcp.tool(name="unreal_get_status")
    async def unreal_get_status(**params: Any) -> dict[str, Any]:
        """Get bridge and editor connection status."""
        return await ctx.dispatcher.call("unreal_get_status", params)

    @mcp.tool(name="unreal_get_version")
    async def unreal_get_version(**params: Any) -> dict[str, Any]:
        """Get Unreal Engine and plugin version info."""
        return await ctx.dispatcher.call("unreal_get_version", params)

    @mcp.tool(name="unreal_get_project_info")
    async def unreal_get_project_info(**params: Any) -> dict[str, Any]:
        """Get current Unreal project information."""
        return await ctx.dispatcher.call("unreal_get_project_info", params)

    @mcp.tool(name="unreal_get_editor_status")
    async def unreal_get_editor_status(**params: Any) -> dict[str, Any]:
        """Get editor play/pie and selection status."""
        return await ctx.dispatcher.call("unreal_get_editor_status", params)

    @mcp.tool(name="unreal_get_current_level")
    async def unreal_get_current_level(**params: Any) -> dict[str, Any]:
        """Get the currently loaded level."""
        return await ctx.dispatcher.call("unreal_get_current_level", params)

    @mcp.tool(name="unreal_get_active_world")
    async def unreal_get_active_world(**params: Any) -> dict[str, Any]:
        """Get the active editor world."""
        return await ctx.dispatcher.call("unreal_get_active_world", params)

    @mcp.tool(name="unreal_get_selected_actors")
    async def unreal_get_selected_actors(**params: Any) -> dict[str, Any]:
        """List currently selected actors."""
        return await ctx.dispatcher.call("unreal_get_selected_actors", params)

    @mcp.tool(name="unreal_list_tools")
    async def unreal_list_tools(**params: Any) -> dict[str, Any]:
        """List tools registered in the Unreal plugin."""
        return await ctx.dispatcher.call("unreal_list_tools", params)

    @mcp.tool(name="unreal_get_logs")
    async def unreal_get_logs(**params: Any) -> dict[str, Any]:
        """Get recent UnrealEngineMCP plugin logs."""
        return await ctx.dispatcher.call("unreal_get_logs", params)

    @mcp.tool(name="unreal_get_errors")
    async def unreal_get_errors(**params: Any) -> dict[str, Any]:
        """Get recent engine/plugin errors."""
        return await ctx.dispatcher.call("unreal_get_errors", params)
