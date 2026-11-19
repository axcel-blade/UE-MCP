"""Auto-registered animation tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_list_animations")
    async def unreal_list_animations(**params: Any) -> dict[str, Any]:
        """List animation sequences."""
        return await ctx.dispatcher.call("unreal_list_animations", params)

    @mcp.tool(name="unreal_get_animation_info")
    async def unreal_get_animation_info(**params: Any) -> dict[str, Any]:
        """Get animation sequence info."""
        return await ctx.dispatcher.call("unreal_get_animation_info", params)

    @mcp.tool(name="unreal_create_animation_blueprint")
    async def unreal_create_animation_blueprint(**params: Any) -> dict[str, Any]:
        """Create an Animation Blueprint."""
        return await ctx.dispatcher.call("unreal_create_animation_blueprint", params)

    @mcp.tool(name="unreal_get_animation_blueprint")
    async def unreal_get_animation_blueprint(**params: Any) -> dict[str, Any]:
        """Get Animation Blueprint info."""
        return await ctx.dispatcher.call("unreal_get_animation_blueprint", params)

    @mcp.tool(name="unreal_create_animation_montage")
    async def unreal_create_animation_montage(**params: Any) -> dict[str, Any]:
        """Create an animation montage."""
        return await ctx.dispatcher.call("unreal_create_animation_montage", params)

    @mcp.tool(name="unreal_set_animation_sequence")
    async def unreal_set_animation_sequence(**params: Any) -> dict[str, Any]:
        """Set montage/sequence references."""
        return await ctx.dispatcher.call("unreal_set_animation_sequence", params)

    @mcp.tool(name="unreal_get_animation_notifies")
    async def unreal_get_animation_notifies(**params: Any) -> dict[str, Any]:
        """Get animation notifies."""
        return await ctx.dispatcher.call("unreal_get_animation_notifies", params)

    @mcp.tool(name="unreal_add_animation_notify")
    async def unreal_add_animation_notify(**params: Any) -> dict[str, Any]:
        """Add an animation notify."""
        return await ctx.dispatcher.call("unreal_add_animation_notify", params)

    @mcp.tool(name="unreal_get_skeleton_assets")
    async def unreal_get_skeleton_assets(**params: Any) -> dict[str, Any]:
        """List skeleton assets."""
        return await ctx.dispatcher.call("unreal_get_skeleton_assets", params)

    @mcp.tool(name="unreal_get_animation_graph")
    async def unreal_get_animation_graph(**params: Any) -> dict[str, Any]:
        """Inspect animation graph nodes."""
        return await ctx.dispatcher.call("unreal_get_animation_graph", params)
