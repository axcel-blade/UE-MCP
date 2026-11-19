"""Auto-registered widgets tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_create_widget_blueprint")
    async def unreal_create_widget_blueprint(**params: Any) -> dict[str, Any]:
        """Create a UMG Widget Blueprint."""
        return await ctx.dispatcher.call("unreal_create_widget_blueprint", params)

    @mcp.tool(name="unreal_get_widget_tree")
    async def unreal_get_widget_tree(**params: Any) -> dict[str, Any]:
        """Get widget tree hierarchy."""
        return await ctx.dispatcher.call("unreal_get_widget_tree", params)

    @mcp.tool(name="unreal_add_widget")
    async def unreal_add_widget(**params: Any) -> dict[str, Any]:
        """Add a widget to a Widget Blueprint."""
        return await ctx.dispatcher.call("unreal_add_widget", params)

    @mcp.tool(name="unreal_remove_widget")
    async def unreal_remove_widget(**params: Any) -> dict[str, Any]:
        """Remove a widget."""
        return await ctx.dispatcher.call("unreal_remove_widget", params)

    @mcp.tool(name="unreal_set_widget_property")
    async def unreal_set_widget_property(**params: Any) -> dict[str, Any]:
        """Set a widget property."""
        return await ctx.dispatcher.call("unreal_set_widget_property", params)

    @mcp.tool(name="unreal_set_widget_position")
    async def unreal_set_widget_position(**params: Any) -> dict[str, Any]:
        """Set widget position."""
        return await ctx.dispatcher.call("unreal_set_widget_position", params)

    @mcp.tool(name="unreal_set_widget_size")
    async def unreal_set_widget_size(**params: Any) -> dict[str, Any]:
        """Set widget size."""
        return await ctx.dispatcher.call("unreal_set_widget_size", params)

    @mcp.tool(name="unreal_set_widget_text")
    async def unreal_set_widget_text(**params: Any) -> dict[str, Any]:
        """Set widget text."""
        return await ctx.dispatcher.call("unreal_set_widget_text", params)

    @mcp.tool(name="unreal_set_widget_color")
    async def unreal_set_widget_color(**params: Any) -> dict[str, Any]:
        """Set widget color."""
        return await ctx.dispatcher.call("unreal_set_widget_color", params)

    @mcp.tool(name="unreal_add_widget_to_viewport")
    async def unreal_add_widget_to_viewport(**params: Any) -> dict[str, Any]:
        """Add a widget instance to the viewport."""
        return await ctx.dispatcher.call("unreal_add_widget_to_viewport", params)

    @mcp.tool(name="unreal_get_widget_details")
    async def unreal_get_widget_details(**params: Any) -> dict[str, Any]:
        """Get widget details."""
        return await ctx.dispatcher.call("unreal_get_widget_details", params)
