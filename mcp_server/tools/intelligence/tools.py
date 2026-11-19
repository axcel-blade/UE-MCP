"""Auto-registered intelligence tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_get_scene_hierarchy")
    async def unreal_get_scene_hierarchy(**params: Any) -> dict[str, Any]:
        """Inspect actor attachment hierarchy."""
        return await ctx.dispatcher.call("unreal_get_scene_hierarchy", params)

    @mcp.tool(name="unreal_get_actor_relationships")
    async def unreal_get_actor_relationships(**params: Any) -> dict[str, Any]:
        """Inspect actor relationships."""
        return await ctx.dispatcher.call("unreal_get_actor_relationships", params)

    @mcp.tool(name="unreal_get_component_hierarchy")
    async def unreal_get_component_hierarchy(**params: Any) -> dict[str, Any]:
        """Inspect component hierarchy."""
        return await ctx.dispatcher.call("unreal_get_component_hierarchy", params)

    @mcp.tool(name="unreal_analyze_asset_dependencies")
    async def unreal_analyze_asset_dependencies(**params: Any) -> dict[str, Any]:
        """Analyze asset dependencies."""
        return await ctx.dispatcher.call("unreal_analyze_asset_dependencies", params)

    @mcp.tool(name="unreal_analyze_blueprint_relationships")
    async def unreal_analyze_blueprint_relationships(**params: Any) -> dict[str, Any]:
        """Analyze Blueprint relationships."""
        return await ctx.dispatcher.call("unreal_analyze_blueprint_relationships", params)

    @mcp.tool(name="unreal_analyze_material_assignments")
    async def unreal_analyze_material_assignments(**params: Any) -> dict[str, Any]:
        """Analyze material assignments in level."""
        return await ctx.dispatcher.call("unreal_analyze_material_assignments", params)

    @mcp.tool(name="unreal_analyze_level_composition")
    async def unreal_analyze_level_composition(**params: Any) -> dict[str, Any]:
        """Analyze level composition."""
        return await ctx.dispatcher.call("unreal_analyze_level_composition", params)

    @mcp.tool(name="unreal_validate_actor_placement")
    async def unreal_validate_actor_placement(**params: Any) -> dict[str, Any]:
        """Validate actor placement."""
        return await ctx.dispatcher.call("unreal_validate_actor_placement", params)

    @mcp.tool(name="unreal_find_duplicate_assets")
    async def unreal_find_duplicate_assets(**params: Any) -> dict[str, Any]:
        """Find potentially duplicate assets."""
        return await ctx.dispatcher.call("unreal_find_duplicate_assets", params)

    @mcp.tool(name="unreal_find_missing_references")
    async def unreal_find_missing_references(**params: Any) -> dict[str, Any]:
        """Find missing references."""
        return await ctx.dispatcher.call("unreal_find_missing_references", params)

    @mcp.tool(name="unreal_find_unused_assets")
    async def unreal_find_unused_assets(**params: Any) -> dict[str, Any]:
        """Find unused assets (bounded scan)."""
        return await ctx.dispatcher.call("unreal_find_unused_assets", params)

    @mcp.tool(name="unreal_get_scene_statistics")
    async def unreal_get_scene_statistics(**params: Any) -> dict[str, Any]:
        """Get scene statistics."""
        return await ctx.dispatcher.call("unreal_get_scene_statistics", params)
