"""Auto-registered rendering tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_capture_viewport")
    async def unreal_capture_viewport(**params: Any) -> dict[str, Any]:
        """Capture the active editor viewport."""
        return await ctx.dispatcher.call("unreal_capture_viewport", params)

    @mcp.tool(name="unreal_capture_screenshot")
    async def unreal_capture_screenshot(**params: Any) -> dict[str, Any]:
        """Capture a high-quality screenshot."""
        return await ctx.dispatcher.call("unreal_capture_screenshot", params)

    @mcp.tool(name="unreal_set_viewport_camera")
    async def unreal_set_viewport_camera(**params: Any) -> dict[str, Any]:
        """Set viewport camera actor/view."""
        return await ctx.dispatcher.call("unreal_set_viewport_camera", params)

    @mcp.tool(name="unreal_set_viewport_location")
    async def unreal_set_viewport_location(**params: Any) -> dict[str, Any]:
        """Set viewport camera location."""
        return await ctx.dispatcher.call("unreal_set_viewport_location", params)

    @mcp.tool(name="unreal_set_viewport_rotation")
    async def unreal_set_viewport_rotation(**params: Any) -> dict[str, Any]:
        """Set viewport camera rotation."""
        return await ctx.dispatcher.call("unreal_set_viewport_rotation", params)

    @mcp.tool(name="unreal_set_viewport_mode")
    async def unreal_set_viewport_mode(**params: Any) -> dict[str, Any]:
        """Set viewport mode/show flags where supported."""
        return await ctx.dispatcher.call("unreal_set_viewport_mode", params)

    @mcp.tool(name="unreal_get_viewport_info")
    async def unreal_get_viewport_info(**params: Any) -> dict[str, Any]:
        """Get viewport camera info."""
        return await ctx.dispatcher.call("unreal_get_viewport_info", params)

    @mcp.tool(name="unreal_render_image")
    async def unreal_render_image(**params: Any) -> dict[str, Any]:
        """Render an image from the current view."""
        return await ctx.dispatcher.call("unreal_render_image", params)

    @mcp.tool(name="unreal_get_render_settings")
    async def unreal_get_render_settings(**params: Any) -> dict[str, Any]:
        """Get project render settings."""
        return await ctx.dispatcher.call("unreal_get_render_settings", params)

    @mcp.tool(name="unreal_set_render_settings")
    async def unreal_set_render_settings(**params: Any) -> dict[str, Any]:
        """Set supported render settings."""
        return await ctx.dispatcher.call("unreal_set_render_settings", params)
