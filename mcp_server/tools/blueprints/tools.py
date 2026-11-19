"""Auto-registered blueprints tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_create_blueprint")
    async def unreal_create_blueprint(**params: Any) -> dict[str, Any]:
        """Create a Blueprint asset."""
        return await ctx.dispatcher.call("unreal_create_blueprint", params)

    @mcp.tool(name="unreal_get_blueprint")
    async def unreal_get_blueprint(**params: Any) -> dict[str, Any]:
        """Get Blueprint asset details."""
        return await ctx.dispatcher.call("unreal_get_blueprint", params)

    @mcp.tool(name="unreal_compile_blueprint")
    async def unreal_compile_blueprint(**params: Any) -> dict[str, Any]:
        """Compile a Blueprint and return diagnostics."""
        return await ctx.dispatcher.call("unreal_compile_blueprint", params)

    @mcp.tool(name="unreal_save_blueprint")
    async def unreal_save_blueprint(**params: Any) -> dict[str, Any]:
        """Save a Blueprint asset."""
        return await ctx.dispatcher.call("unreal_save_blueprint", params)

    @mcp.tool(name="unreal_delete_blueprint")
    async def unreal_delete_blueprint(**params: Any) -> dict[str, Any]:
        """Delete a Blueprint asset."""
        return await ctx.dispatcher.call("unreal_delete_blueprint", params)

    @mcp.tool(name="unreal_add_blueprint_variable")
    async def unreal_add_blueprint_variable(**params: Any) -> dict[str, Any]:
        """Add a Blueprint variable."""
        return await ctx.dispatcher.call("unreal_add_blueprint_variable", params)

    @mcp.tool(name="unreal_remove_blueprint_variable")
    async def unreal_remove_blueprint_variable(**params: Any) -> dict[str, Any]:
        """Remove a Blueprint variable."""
        return await ctx.dispatcher.call("unreal_remove_blueprint_variable", params)

    @mcp.tool(name="unreal_get_blueprint_variables")
    async def unreal_get_blueprint_variables(**params: Any) -> dict[str, Any]:
        """List Blueprint variables."""
        return await ctx.dispatcher.call("unreal_get_blueprint_variables", params)

    @mcp.tool(name="unreal_add_blueprint_function")
    async def unreal_add_blueprint_function(**params: Any) -> dict[str, Any]:
        """Add a Blueprint function graph."""
        return await ctx.dispatcher.call("unreal_add_blueprint_function", params)

    @mcp.tool(name="unreal_get_blueprint_functions")
    async def unreal_get_blueprint_functions(**params: Any) -> dict[str, Any]:
        """List Blueprint functions."""
        return await ctx.dispatcher.call("unreal_get_blueprint_functions", params)

    @mcp.tool(name="unreal_add_blueprint_event")
    async def unreal_add_blueprint_event(**params: Any) -> dict[str, Any]:
        """Add a Blueprint event node."""
        return await ctx.dispatcher.call("unreal_add_blueprint_event", params)

    @mcp.tool(name="unreal_get_blueprint_graphs")
    async def unreal_get_blueprint_graphs(**params: Any) -> dict[str, Any]:
        """List Blueprint graphs."""
        return await ctx.dispatcher.call("unreal_get_blueprint_graphs", params)

    @mcp.tool(name="unreal_get_blueprint_nodes")
    async def unreal_get_blueprint_nodes(**params: Any) -> dict[str, Any]:
        """List nodes in a Blueprint graph."""
        return await ctx.dispatcher.call("unreal_get_blueprint_nodes", params)

    @mcp.tool(name="unreal_create_blueprint_node")
    async def unreal_create_blueprint_node(**params: Any) -> dict[str, Any]:
        """Create a Blueprint node."""
        return await ctx.dispatcher.call("unreal_create_blueprint_node", params)

    @mcp.tool(name="unreal_connect_blueprint_nodes")
    async def unreal_connect_blueprint_nodes(**params: Any) -> dict[str, Any]:
        """Connect two Blueprint node pins."""
        return await ctx.dispatcher.call("unreal_connect_blueprint_nodes", params)

    @mcp.tool(name="unreal_disconnect_blueprint_nodes")
    async def unreal_disconnect_blueprint_nodes(**params: Any) -> dict[str, Any]:
        """Disconnect Blueprint node pins."""
        return await ctx.dispatcher.call("unreal_disconnect_blueprint_nodes", params)

    @mcp.tool(name="unreal_set_blueprint_node_property")
    async def unreal_set_blueprint_node_property(**params: Any) -> dict[str, Any]:
        """Set a Blueprint node property."""
        return await ctx.dispatcher.call("unreal_set_blueprint_node_property", params)

    @mcp.tool(name="unreal_delete_blueprint_node")
    async def unreal_delete_blueprint_node(**params: Any) -> dict[str, Any]:
        """Delete a Blueprint node."""
        return await ctx.dispatcher.call("unreal_delete_blueprint_node", params)

    @mcp.tool(name="unreal_get_blueprint_node_details")
    async def unreal_get_blueprint_node_details(**params: Any) -> dict[str, Any]:
        """Get Blueprint node/pin details."""
        return await ctx.dispatcher.call("unreal_get_blueprint_node_details", params)

    @mcp.tool(name="unreal_create_blueprint_macro")
    async def unreal_create_blueprint_macro(**params: Any) -> dict[str, Any]:
        """Create a Blueprint macro graph."""
        return await ctx.dispatcher.call("unreal_create_blueprint_macro", params)

    @mcp.tool(name="unreal_add_blueprint_component")
    async def unreal_add_blueprint_component(**params: Any) -> dict[str, Any]:
        """Add a component to a Blueprint SCS."""
        return await ctx.dispatcher.call("unreal_add_blueprint_component", params)

    @mcp.tool(name="unreal_set_blueprint_parent_class")
    async def unreal_set_blueprint_parent_class(**params: Any) -> dict[str, Any]:
        """Set Blueprint parent class."""
        return await ctx.dispatcher.call("unreal_set_blueprint_parent_class", params)
