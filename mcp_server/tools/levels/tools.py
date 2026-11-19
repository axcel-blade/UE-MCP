"""Auto-registered levels tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_create_level")
    async def unreal_create_level(**params: Any) -> dict[str, Any]:
        """Create a new level asset."""
        return await ctx.dispatcher.call("unreal_create_level", params)

    @mcp.tool(name="unreal_open_level")
    async def unreal_open_level(**params: Any) -> dict[str, Any]:
        """Open a level."""
        return await ctx.dispatcher.call("unreal_open_level", params)

    @mcp.tool(name="unreal_save_level")
    async def unreal_save_level(**params: Any) -> dict[str, Any]:
        """Save the current level."""
        return await ctx.dispatcher.call("unreal_save_level", params)

    @mcp.tool(name="unreal_get_levels")
    async def unreal_get_levels(**params: Any) -> dict[str, Any]:
        """List levels in the project."""
        return await ctx.dispatcher.call("unreal_get_levels", params)

    @mcp.tool(name="unreal_get_world_info")
    async def unreal_get_world_info(**params: Any) -> dict[str, Any]:
        """Get world and level info."""
        return await ctx.dispatcher.call("unreal_get_world_info", params)

    @mcp.tool(name="unreal_set_world_settings")
    async def unreal_set_world_settings(**params: Any) -> dict[str, Any]:
        """Set supported world settings."""
        return await ctx.dispatcher.call("unreal_set_world_settings", params)

    @mcp.tool(name="unreal_create_sublevel")
    async def unreal_create_sublevel(**params: Any) -> dict[str, Any]:
        """Create a streaming sublevel."""
        return await ctx.dispatcher.call("unreal_create_sublevel", params)

    @mcp.tool(name="unreal_manage_level_visibility")
    async def unreal_manage_level_visibility(**params: Any) -> dict[str, Any]:
        """Show/hide a streaming level."""
        return await ctx.dispatcher.call("unreal_manage_level_visibility", params)

    @mcp.tool(name="unreal_list_level_actors")
    async def unreal_list_level_actors(**params: Any) -> dict[str, Any]:
        """List actors for a level."""
        return await ctx.dispatcher.call("unreal_list_level_actors", params)

    @mcp.tool(name="unreal_create_world_partition_info")
    async def unreal_create_world_partition_info(**params: Any) -> dict[str, Any]:
        """Inspect world partition info when available."""
        return await ctx.dispatcher.call("unreal_create_world_partition_info", params)
