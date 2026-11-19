"""Auto-registered niagara tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_list_niagara_systems")
    async def unreal_list_niagara_systems(**params: Any) -> dict[str, Any]:
        """List Niagara systems."""
        return await ctx.dispatcher.call("unreal_list_niagara_systems", params)

    @mcp.tool(name="unreal_get_niagara_info")
    async def unreal_get_niagara_info(**params: Any) -> dict[str, Any]:
        """Get Niagara system info."""
        return await ctx.dispatcher.call("unreal_get_niagara_info", params)

    @mcp.tool(name="unreal_create_niagara_system")
    async def unreal_create_niagara_system(**params: Any) -> dict[str, Any]:
        """Create a Niagara system asset."""
        return await ctx.dispatcher.call("unreal_create_niagara_system", params)

    @mcp.tool(name="unreal_spawn_niagara_system")
    async def unreal_spawn_niagara_system(**params: Any) -> dict[str, Any]:
        """Spawn a Niagara actor."""
        return await ctx.dispatcher.call("unreal_spawn_niagara_system", params)

    @mcp.tool(name="unreal_set_niagara_parameter")
    async def unreal_set_niagara_parameter(**params: Any) -> dict[str, Any]:
        """Set a Niagara user parameter."""
        return await ctx.dispatcher.call("unreal_set_niagara_parameter", params)

    @mcp.tool(name="unreal_get_niagara_parameters")
    async def unreal_get_niagara_parameters(**params: Any) -> dict[str, Any]:
        """Get Niagara parameters."""
        return await ctx.dispatcher.call("unreal_get_niagara_parameters", params)

    @mcp.tool(name="unreal_save_niagara_system")
    async def unreal_save_niagara_system(**params: Any) -> dict[str, Any]:
        """Save a Niagara system."""
        return await ctx.dispatcher.call("unreal_save_niagara_system", params)
