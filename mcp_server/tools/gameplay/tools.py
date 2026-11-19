"""Auto-registered gameplay tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_get_game_mode")
    async def unreal_get_game_mode(**params: Any) -> dict[str, Any]:
        """Get project/default game mode."""
        return await ctx.dispatcher.call("unreal_get_game_mode", params)

    @mcp.tool(name="unreal_set_game_mode")
    async def unreal_set_game_mode(**params: Any) -> dict[str, Any]:
        """Set default game mode class."""
        return await ctx.dispatcher.call("unreal_set_game_mode", params)

    @mcp.tool(name="unreal_get_game_instance")
    async def unreal_get_game_instance(**params: Any) -> dict[str, Any]:
        """Get game instance class info."""
        return await ctx.dispatcher.call("unreal_get_game_instance", params)

    @mcp.tool(name="unreal_get_game_state")
    async def unreal_get_game_state(**params: Any) -> dict[str, Any]:
        """Get game state class info."""
        return await ctx.dispatcher.call("unreal_get_game_state", params)

    @mcp.tool(name="unreal_get_player_controller")
    async def unreal_get_player_controller(**params: Any) -> dict[str, Any]:
        """Get player controller info."""
        return await ctx.dispatcher.call("unreal_get_player_controller", params)

    @mcp.tool(name="unreal_get_character_info")
    async def unreal_get_character_info(**params: Any) -> dict[str, Any]:
        """Get selected/pawn character info."""
        return await ctx.dispatcher.call("unreal_get_character_info", params)

    @mcp.tool(name="unreal_get_ai_controller")
    async def unreal_get_ai_controller(**params: Any) -> dict[str, Any]:
        """Get AI controller info."""
        return await ctx.dispatcher.call("unreal_get_ai_controller", params)

    @mcp.tool(name="unreal_get_behavior_tree")
    async def unreal_get_behavior_tree(**params: Any) -> dict[str, Any]:
        """Get behavior tree asset info."""
        return await ctx.dispatcher.call("unreal_get_behavior_tree", params)

    @mcp.tool(name="unreal_get_blackboard")
    async def unreal_get_blackboard(**params: Any) -> dict[str, Any]:
        """Get blackboard asset info."""
        return await ctx.dispatcher.call("unreal_get_blackboard", params)

    @mcp.tool(name="unreal_get_gameplay_tags")
    async def unreal_get_gameplay_tags(**params: Any) -> dict[str, Any]:
        """List gameplay tags."""
        return await ctx.dispatcher.call("unreal_get_gameplay_tags", params)

    @mcp.tool(name="unreal_get_input_mappings")
    async def unreal_get_input_mappings(**params: Any) -> dict[str, Any]:
        """Get input action/axis mappings."""
        return await ctx.dispatcher.call("unreal_get_input_mappings", params)
