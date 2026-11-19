"""Auto-registered pipeline tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_import_blender_fbx")
    async def unreal_import_blender_fbx(**params: Any) -> dict[str, Any]:
        """Import an FBX exported from Blender with validation."""
        return await ctx.dispatcher.call("unreal_import_blender_fbx", params)

    @mcp.tool(name="unreal_validate_blender_import")
    async def unreal_validate_blender_import(**params: Any) -> dict[str, Any]:
        """Validate Blender export conventions for Unreal."""
        return await ctx.dispatcher.call("unreal_validate_blender_import", params)

    @mcp.tool(name="unreal_reimport_blender_asset")
    async def unreal_reimport_blender_asset(**params: Any) -> dict[str, Any]:
        """Reimport a previously imported Blender asset."""
        return await ctx.dispatcher.call("unreal_reimport_blender_asset", params)
