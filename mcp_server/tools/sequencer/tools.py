"""Auto-registered sequencer tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_create_level_sequence")
    async def unreal_create_level_sequence(**params: Any) -> dict[str, Any]:
        """Create a Level Sequence."""
        return await ctx.dispatcher.call("unreal_create_level_sequence", params)

    @mcp.tool(name="unreal_get_level_sequences")
    async def unreal_get_level_sequences(**params: Any) -> dict[str, Any]:
        """List Level Sequences."""
        return await ctx.dispatcher.call("unreal_get_level_sequences", params)

    @mcp.tool(name="unreal_add_sequence_track")
    async def unreal_add_sequence_track(**params: Any) -> dict[str, Any]:
        """Add a sequence track."""
        return await ctx.dispatcher.call("unreal_add_sequence_track", params)

    @mcp.tool(name="unreal_add_sequence_section")
    async def unreal_add_sequence_section(**params: Any) -> dict[str, Any]:
        """Add a sequence section."""
        return await ctx.dispatcher.call("unreal_add_sequence_section", params)

    @mcp.tool(name="unreal_add_camera")
    async def unreal_add_camera(**params: Any) -> dict[str, Any]:
        """Add a camera to the level/sequence."""
        return await ctx.dispatcher.call("unreal_add_camera", params)

    @mcp.tool(name="unreal_add_camera_cut")
    async def unreal_add_camera_cut(**params: Any) -> dict[str, Any]:
        """Add a camera cut."""
        return await ctx.dispatcher.call("unreal_add_camera_cut", params)

    @mcp.tool(name="unreal_set_sequence_duration")
    async def unreal_set_sequence_duration(**params: Any) -> dict[str, Any]:
        """Set sequence duration."""
        return await ctx.dispatcher.call("unreal_set_sequence_duration", params)

    @mcp.tool(name="unreal_set_keyframe")
    async def unreal_set_keyframe(**params: Any) -> dict[str, Any]:
        """Set a transform/property keyframe."""
        return await ctx.dispatcher.call("unreal_set_keyframe", params)

    @mcp.tool(name="unreal_get_sequence_info")
    async def unreal_get_sequence_info(**params: Any) -> dict[str, Any]:
        """Get sequence info."""
        return await ctx.dispatcher.call("unreal_get_sequence_info", params)

    @mcp.tool(name="unreal_render_sequence")
    async def unreal_render_sequence(**params: Any) -> dict[str, Any]:
        """Queue a sequence render/export."""
        return await ctx.dispatcher.call("unreal_render_sequence", params)
