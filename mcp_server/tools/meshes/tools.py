"""Auto-registered meshes tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_get_mesh_info")
    async def unreal_get_mesh_info(**params: Any) -> dict[str, Any]:
        """Get static mesh info."""
        return await ctx.dispatcher.call("unreal_get_mesh_info", params)

    @mcp.tool(name="unreal_create_static_mesh")
    async def unreal_create_static_mesh(**params: Any) -> dict[str, Any]:
        """Create a basic static mesh asset where supported."""
        return await ctx.dispatcher.call("unreal_create_static_mesh", params)

    @mcp.tool(name="unreal_get_mesh_bounds")
    async def unreal_get_mesh_bounds(**params: Any) -> dict[str, Any]:
        """Get mesh bounds."""
        return await ctx.dispatcher.call("unreal_get_mesh_bounds", params)

    @mcp.tool(name="unreal_get_mesh_sections")
    async def unreal_get_mesh_sections(**params: Any) -> dict[str, Any]:
        """Get mesh sections."""
        return await ctx.dispatcher.call("unreal_get_mesh_sections", params)

    @mcp.tool(name="unreal_get_mesh_materials")
    async def unreal_get_mesh_materials(**params: Any) -> dict[str, Any]:
        """Get mesh materials."""
        return await ctx.dispatcher.call("unreal_get_mesh_materials", params)

    @mcp.tool(name="unreal_set_mesh_material")
    async def unreal_set_mesh_material(**params: Any) -> dict[str, Any]:
        """Set a mesh material slot."""
        return await ctx.dispatcher.call("unreal_set_mesh_material", params)

    @mcp.tool(name="unreal_generate_collision")
    async def unreal_generate_collision(**params: Any) -> dict[str, Any]:
        """Generate mesh collision."""
        return await ctx.dispatcher.call("unreal_generate_collision", params)

    @mcp.tool(name="unreal_get_collision_info")
    async def unreal_get_collision_info(**params: Any) -> dict[str, Any]:
        """Get mesh collision info."""
        return await ctx.dispatcher.call("unreal_get_collision_info", params)

    @mcp.tool(name="unreal_set_mesh_lod")
    async def unreal_set_mesh_lod(**params: Any) -> dict[str, Any]:
        """Configure mesh LOD settings."""
        return await ctx.dispatcher.call("unreal_set_mesh_lod", params)

    @mcp.tool(name="unreal_get_skeletal_mesh_info")
    async def unreal_get_skeletal_mesh_info(**params: Any) -> dict[str, Any]:
        """Get skeletal mesh info."""
        return await ctx.dispatcher.call("unreal_get_skeletal_mesh_info", params)

    @mcp.tool(name="unreal_get_skeleton_info")
    async def unreal_get_skeleton_info(**params: Any) -> dict[str, Any]:
        """Get skeleton info."""
        return await ctx.dispatcher.call("unreal_get_skeleton_info", params)

    @mcp.tool(name="unreal_get_bone_hierarchy")
    async def unreal_get_bone_hierarchy(**params: Any) -> dict[str, Any]:
        """Get bone hierarchy."""
        return await ctx.dispatcher.call("unreal_get_bone_hierarchy", params)

    @mcp.tool(name="unreal_set_mesh_collision")
    async def unreal_set_mesh_collision(**params: Any) -> dict[str, Any]:
        """Set mesh collision profile/settings."""
        return await ctx.dispatcher.call("unreal_set_mesh_collision", params)
