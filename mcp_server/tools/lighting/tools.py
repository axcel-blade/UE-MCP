"""Auto-registered lighting tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:

    @mcp.tool(name="unreal_create_directional_light")
    async def unreal_create_directional_light(**params: Any) -> dict[str, Any]:
        """Create a directional light."""
        return await ctx.dispatcher.call("unreal_create_directional_light", params)

    @mcp.tool(name="unreal_create_point_light")
    async def unreal_create_point_light(**params: Any) -> dict[str, Any]:
        """Create a point light."""
        return await ctx.dispatcher.call("unreal_create_point_light", params)

    @mcp.tool(name="unreal_create_spot_light")
    async def unreal_create_spot_light(**params: Any) -> dict[str, Any]:
        """Create a spot light."""
        return await ctx.dispatcher.call("unreal_create_spot_light", params)

    @mcp.tool(name="unreal_create_rect_light")
    async def unreal_create_rect_light(**params: Any) -> dict[str, Any]:
        """Create a rect light."""
        return await ctx.dispatcher.call("unreal_create_rect_light", params)

    @mcp.tool(name="unreal_create_sky_light")
    async def unreal_create_sky_light(**params: Any) -> dict[str, Any]:
        """Create a sky light."""
        return await ctx.dispatcher.call("unreal_create_sky_light", params)

    @mcp.tool(name="unreal_create_sky_atmosphere")
    async def unreal_create_sky_atmosphere(**params: Any) -> dict[str, Any]:
        """Create a sky atmosphere actor."""
        return await ctx.dispatcher.call("unreal_create_sky_atmosphere", params)

    @mcp.tool(name="unreal_create_exponential_height_fog")
    async def unreal_create_exponential_height_fog(**params: Any) -> dict[str, Any]:
        """Create exponential height fog."""
        return await ctx.dispatcher.call("unreal_create_exponential_height_fog", params)

    @mcp.tool(name="unreal_set_light_intensity")
    async def unreal_set_light_intensity(**params: Any) -> dict[str, Any]:
        """Set light intensity."""
        return await ctx.dispatcher.call("unreal_set_light_intensity", params)

    @mcp.tool(name="unreal_set_light_color")
    async def unreal_set_light_color(**params: Any) -> dict[str, Any]:
        """Set light color."""
        return await ctx.dispatcher.call("unreal_set_light_color", params)

    @mcp.tool(name="unreal_set_light_temperature")
    async def unreal_set_light_temperature(**params: Any) -> dict[str, Any]:
        """Set light temperature."""
        return await ctx.dispatcher.call("unreal_set_light_temperature", params)

    @mcp.tool(name="unreal_set_shadow_settings")
    async def unreal_set_shadow_settings(**params: Any) -> dict[str, Any]:
        """Set light shadow settings."""
        return await ctx.dispatcher.call("unreal_set_shadow_settings", params)

    @mcp.tool(name="unreal_set_environment_settings")
    async def unreal_set_environment_settings(**params: Any) -> dict[str, Any]:
        """Set environment/fog/sky settings."""
        return await ctx.dispatcher.call("unreal_set_environment_settings", params)

    @mcp.tool(name="unreal_get_lighting_info")
    async def unreal_get_lighting_info(**params: Any) -> dict[str, Any]:
        """Get lighting actors info."""
        return await ctx.dispatcher.call("unreal_get_lighting_info", params)
