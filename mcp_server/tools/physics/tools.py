"""Auto-registered physics tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_set_physics_enabled")
    async def unreal_set_physics_enabled(**params: Any) -> dict[str, Any]:
        """Enable/disable physics on an actor/component."""
        return await ctx.dispatcher.call("unreal_set_physics_enabled", params)

    @mcp.tool(name="unreal_set_simulate_physics")
    async def unreal_set_simulate_physics(**params: Any) -> dict[str, Any]:
        """Toggle simulate physics."""
        return await ctx.dispatcher.call("unreal_set_simulate_physics", params)

    @mcp.tool(name="unreal_set_gravity")
    async def unreal_set_gravity(**params: Any) -> dict[str, Any]:
        """Set gravity enabled/scale."""
        return await ctx.dispatcher.call("unreal_set_gravity", params)

    @mcp.tool(name="unreal_set_mass")
    async def unreal_set_mass(**params: Any) -> dict[str, Any]:
        """Set mass override."""
        return await ctx.dispatcher.call("unreal_set_mass", params)

    @mcp.tool(name="unreal_set_linear_velocity")
    async def unreal_set_linear_velocity(**params: Any) -> dict[str, Any]:
        """Set linear velocity."""
        return await ctx.dispatcher.call("unreal_set_linear_velocity", params)

    @mcp.tool(name="unreal_set_angular_velocity")
    async def unreal_set_angular_velocity(**params: Any) -> dict[str, Any]:
        """Set angular velocity."""
        return await ctx.dispatcher.call("unreal_set_angular_velocity", params)

    @mcp.tool(name="unreal_set_collision_profile")
    async def unreal_set_collision_profile(**params: Any) -> dict[str, Any]:
        """Set collision profile name."""
        return await ctx.dispatcher.call("unreal_set_collision_profile", params)

    @mcp.tool(name="unreal_get_physics_info")
    async def unreal_get_physics_info(**params: Any) -> dict[str, Any]:
        """Get physics info for an actor."""
        return await ctx.dispatcher.call("unreal_get_physics_info", params)

    @mcp.tool(name="unreal_get_collision_channels")
    async def unreal_get_collision_channels(**params: Any) -> dict[str, Any]:
        """Get collision channel names."""
        return await ctx.dispatcher.call("unreal_get_collision_channels", params)
