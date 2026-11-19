"""Auto-registered materials tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_create_material")
    async def unreal_create_material(**params: Any) -> dict[str, Any]:
        """Create a material asset."""
        return await ctx.dispatcher.call("unreal_create_material", params)

    @mcp.tool(name="unreal_create_material_instance")
    async def unreal_create_material_instance(**params: Any) -> dict[str, Any]:
        """Create a material instance."""
        return await ctx.dispatcher.call("unreal_create_material_instance", params)

    @mcp.tool(name="unreal_get_material")
    async def unreal_get_material(**params: Any) -> dict[str, Any]:
        """Get material details."""
        return await ctx.dispatcher.call("unreal_get_material", params)

    @mcp.tool(name="unreal_get_material_parameters")
    async def unreal_get_material_parameters(**params: Any) -> dict[str, Any]:
        """List material parameters."""
        return await ctx.dispatcher.call("unreal_get_material_parameters", params)

    @mcp.tool(name="unreal_set_material_parameter")
    async def unreal_set_material_parameter(**params: Any) -> dict[str, Any]:
        """Set a material instance parameter."""
        return await ctx.dispatcher.call("unreal_set_material_parameter", params)

    @mcp.tool(name="unreal_add_material_expression")
    async def unreal_add_material_expression(**params: Any) -> dict[str, Any]:
        """Add a material expression."""
        return await ctx.dispatcher.call("unreal_add_material_expression", params)

    @mcp.tool(name="unreal_connect_material_nodes")
    async def unreal_connect_material_nodes(**params: Any) -> dict[str, Any]:
        """Connect material expressions."""
        return await ctx.dispatcher.call("unreal_connect_material_nodes", params)

    @mcp.tool(name="unreal_disconnect_material_nodes")
    async def unreal_disconnect_material_nodes(**params: Any) -> dict[str, Any]:
        """Disconnect material expressions."""
        return await ctx.dispatcher.call("unreal_disconnect_material_nodes", params)

    @mcp.tool(name="unreal_delete_material_expression")
    async def unreal_delete_material_expression(**params: Any) -> dict[str, Any]:
        """Delete a material expression."""
        return await ctx.dispatcher.call("unreal_delete_material_expression", params)

    @mcp.tool(name="unreal_compile_material")
    async def unreal_compile_material(**params: Any) -> dict[str, Any]:
        """Compile a material."""
        return await ctx.dispatcher.call("unreal_compile_material", params)

    @mcp.tool(name="unreal_save_material")
    async def unreal_save_material(**params: Any) -> dict[str, Any]:
        """Save a material asset."""
        return await ctx.dispatcher.call("unreal_save_material", params)

    @mcp.tool(name="unreal_assign_material")
    async def unreal_assign_material(**params: Any) -> dict[str, Any]:
        """Assign a material to a mesh component."""
        return await ctx.dispatcher.call("unreal_assign_material", params)
