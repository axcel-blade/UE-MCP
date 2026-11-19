"""Auto-registered project tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_get_project_settings")
    async def unreal_get_project_settings(**params: Any) -> dict[str, Any]:
        """Get selected project settings."""
        return await ctx.dispatcher.call("unreal_get_project_settings", params)

    @mcp.tool(name="unreal_get_engine_settings")
    async def unreal_get_engine_settings(**params: Any) -> dict[str, Any]:
        """Get engine settings subset."""
        return await ctx.dispatcher.call("unreal_get_engine_settings", params)

    @mcp.tool(name="unreal_get_input_settings")
    async def unreal_get_input_settings(**params: Any) -> dict[str, Any]:
        """Get input settings."""
        return await ctx.dispatcher.call("unreal_get_input_settings", params)

    @mcp.tool(name="unreal_get_rendering_settings")
    async def unreal_get_rendering_settings(**params: Any) -> dict[str, Any]:
        """Get rendering settings."""
        return await ctx.dispatcher.call("unreal_get_rendering_settings", params)

    @mcp.tool(name="unreal_get_physics_settings")
    async def unreal_get_physics_settings(**params: Any) -> dict[str, Any]:
        """Get physics settings."""
        return await ctx.dispatcher.call("unreal_get_physics_settings", params)

    @mcp.tool(name="unreal_get_plugins")
    async def unreal_get_plugins(**params: Any) -> dict[str, Any]:
        """List enabled plugins."""
        return await ctx.dispatcher.call("unreal_get_plugins", params)

    @mcp.tool(name="unreal_get_build_configuration")
    async def unreal_get_build_configuration(**params: Any) -> dict[str, Any]:
        """Get build configuration info."""
        return await ctx.dispatcher.call("unreal_get_build_configuration", params)

    @mcp.tool(name="unreal_get_project_modules")
    async def unreal_get_project_modules(**params: Any) -> dict[str, Any]:
        """List project modules."""
        return await ctx.dispatcher.call("unreal_get_project_modules", params)
