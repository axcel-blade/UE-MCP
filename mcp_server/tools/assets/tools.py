"""Auto-registered assets tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_list_assets")
    async def unreal_list_assets(**params: Any) -> dict[str, Any]:
        """List assets under a content path."""
        return await ctx.dispatcher.call("unreal_list_assets", params)

    @mcp.tool(name="unreal_search_assets")
    async def unreal_search_assets(**params: Any) -> dict[str, Any]:
        """Search assets by name/class."""
        return await ctx.dispatcher.call("unreal_search_assets", params)

    @mcp.tool(name="unreal_get_asset_info")
    async def unreal_get_asset_info(**params: Any) -> dict[str, Any]:
        """Get asset metadata."""
        return await ctx.dispatcher.call("unreal_get_asset_info", params)

    @mcp.tool(name="unreal_import_asset")
    async def unreal_import_asset(**params: Any) -> dict[str, Any]:
        """Import an external asset file."""
        return await ctx.dispatcher.call("unreal_import_asset", params)

    @mcp.tool(name="unreal_reimport_asset")
    async def unreal_reimport_asset(**params: Any) -> dict[str, Any]:
        """Reimport an asset."""
        return await ctx.dispatcher.call("unreal_reimport_asset", params)

    @mcp.tool(name="unreal_duplicate_asset")
    async def unreal_duplicate_asset(**params: Any) -> dict[str, Any]:
        """Duplicate an asset."""
        return await ctx.dispatcher.call("unreal_duplicate_asset", params)

    @mcp.tool(name="unreal_rename_asset")
    async def unreal_rename_asset(**params: Any) -> dict[str, Any]:
        """Rename an asset."""
        return await ctx.dispatcher.call("unreal_rename_asset", params)

    @mcp.tool(name="unreal_move_asset")
    async def unreal_move_asset(**params: Any) -> dict[str, Any]:
        """Move an asset."""
        return await ctx.dispatcher.call("unreal_move_asset", params)

    @mcp.tool(name="unreal_delete_asset")
    async def unreal_delete_asset(**params: Any) -> dict[str, Any]:
        """Delete an asset."""
        return await ctx.dispatcher.call("unreal_delete_asset", params)

    @mcp.tool(name="unreal_save_asset")
    async def unreal_save_asset(**params: Any) -> dict[str, Any]:
        """Save an asset."""
        return await ctx.dispatcher.call("unreal_save_asset", params)

    @mcp.tool(name="unreal_get_asset_references")
    async def unreal_get_asset_references(**params: Any) -> dict[str, Any]:
        """Get asset referencers."""
        return await ctx.dispatcher.call("unreal_get_asset_references", params)

    @mcp.tool(name="unreal_get_asset_dependencies")
    async def unreal_get_asset_dependencies(**params: Any) -> dict[str, Any]:
        """Get asset dependencies."""
        return await ctx.dispatcher.call("unreal_get_asset_dependencies", params)

    @mcp.tool(name="unreal_get_asset_thumbnail")
    async def unreal_get_asset_thumbnail(**params: Any) -> dict[str, Any]:
        """Export asset thumbnail path when available."""
        return await ctx.dispatcher.call("unreal_get_asset_thumbnail", params)

    @mcp.tool(name="unreal_create_folder")
    async def unreal_create_folder(**params: Any) -> dict[str, Any]:
        """Create a content browser folder."""
        return await ctx.dispatcher.call("unreal_create_folder", params)
