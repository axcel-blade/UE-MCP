"""Auto-registered actors tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_spawn_actor")
    async def unreal_spawn_actor(**params: Any) -> dict[str, Any]:
        """Spawn an actor in the current level."""
        return await ctx.dispatcher.call("unreal_spawn_actor", params)

    @mcp.tool(name="unreal_delete_actor")
    async def unreal_delete_actor(**params: Any) -> dict[str, Any]:
        """Delete an actor by name or path."""
        return await ctx.dispatcher.call("unreal_delete_actor", params)

    @mcp.tool(name="unreal_duplicate_actor")
    async def unreal_duplicate_actor(**params: Any) -> dict[str, Any]:
        """Duplicate an actor."""
        return await ctx.dispatcher.call("unreal_duplicate_actor", params)

    @mcp.tool(name="unreal_find_actor")
    async def unreal_find_actor(**params: Any) -> dict[str, Any]:
        """Find actors by name/label/class."""
        return await ctx.dispatcher.call("unreal_find_actor", params)

    @mcp.tool(name="unreal_get_actor_details")
    async def unreal_get_actor_details(**params: Any) -> dict[str, Any]:
        """Get detailed actor information."""
        return await ctx.dispatcher.call("unreal_get_actor_details", params)

    @mcp.tool(name="unreal_get_all_actors")
    async def unreal_get_all_actors(**params: Any) -> dict[str, Any]:
        """List actors in the current world."""
        return await ctx.dispatcher.call("unreal_get_all_actors", params)

    @mcp.tool(name="unreal_set_actor_transform")
    async def unreal_set_actor_transform(**params: Any) -> dict[str, Any]:
        """Set actor location/rotation/scale."""
        return await ctx.dispatcher.call("unreal_set_actor_transform", params)

    @mcp.tool(name="unreal_get_actor_transform")
    async def unreal_get_actor_transform(**params: Any) -> dict[str, Any]:
        """Get actor transform."""
        return await ctx.dispatcher.call("unreal_get_actor_transform", params)

    @mcp.tool(name="unreal_set_actor_location")
    async def unreal_set_actor_location(**params: Any) -> dict[str, Any]:
        """Set actor location."""
        return await ctx.dispatcher.call("unreal_set_actor_location", params)

    @mcp.tool(name="unreal_set_actor_rotation")
    async def unreal_set_actor_rotation(**params: Any) -> dict[str, Any]:
        """Set actor rotation."""
        return await ctx.dispatcher.call("unreal_set_actor_rotation", params)

    @mcp.tool(name="unreal_set_actor_scale")
    async def unreal_set_actor_scale(**params: Any) -> dict[str, Any]:
        """Set actor scale."""
        return await ctx.dispatcher.call("unreal_set_actor_scale", params)

    @mcp.tool(name="unreal_rename_actor")
    async def unreal_rename_actor(**params: Any) -> dict[str, Any]:
        """Rename an actor label."""
        return await ctx.dispatcher.call("unreal_rename_actor", params)

    @mcp.tool(name="unreal_set_actor_visibility")
    async def unreal_set_actor_visibility(**params: Any) -> dict[str, Any]:
        """Set actor visibility."""
        return await ctx.dispatcher.call("unreal_set_actor_visibility", params)

    @mcp.tool(name="unreal_set_actor_mobility")
    async def unreal_set_actor_mobility(**params: Any) -> dict[str, Any]:
        """Set actor mobility."""
        return await ctx.dispatcher.call("unreal_set_actor_mobility", params)

    @mcp.tool(name="unreal_attach_actor")
    async def unreal_attach_actor(**params: Any) -> dict[str, Any]:
        """Attach an actor to another."""
        return await ctx.dispatcher.call("unreal_attach_actor", params)

    @mcp.tool(name="unreal_detach_actor")
    async def unreal_detach_actor(**params: Any) -> dict[str, Any]:
        """Detach an actor from its parent."""
        return await ctx.dispatcher.call("unreal_detach_actor", params)

    @mcp.tool(name="unreal_add_component")
    async def unreal_add_component(**params: Any) -> dict[str, Any]:
        """Add a component to an actor."""
        return await ctx.dispatcher.call("unreal_add_component", params)

    @mcp.tool(name="unreal_remove_component")
    async def unreal_remove_component(**params: Any) -> dict[str, Any]:
        """Remove a component from an actor."""
        return await ctx.dispatcher.call("unreal_remove_component", params)

    @mcp.tool(name="unreal_get_actor_components")
    async def unreal_get_actor_components(**params: Any) -> dict[str, Any]:
        """List actor components."""
        return await ctx.dispatcher.call("unreal_get_actor_components", params)
