"""Register MCP resources."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register_resources(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.resource("unreal://project/info")
    async def project_info() -> str:
        res = await ctx.dispatcher.call("unreal_get_project_info", {})
        return json.dumps(res, indent=2)

    @mcp.resource("unreal://project/settings")
    async def project_settings() -> str:
        res = await ctx.dispatcher.call("unreal_get_project_settings", {})
        return json.dumps(res, indent=2)

    @mcp.resource("unreal://world/current")
    async def world_current() -> str:
        res = await ctx.dispatcher.call("unreal_get_world_info", {})
        return json.dumps(res, indent=2)

    @mcp.resource("unreal://world/actors")
    async def world_actors() -> str:
        res = await ctx.dispatcher.call("unreal_get_all_actors", {"limit": 200})
        return json.dumps(res, indent=2)

    @mcp.resource("unreal://assets/index")
    async def assets_index() -> str:
        res = await ctx.dispatcher.call("unreal_list_assets", {"path": "/Game", "limit": 100})
        return json.dumps(res, indent=2)

    @mcp.resource("unreal://blueprints/index")
    async def blueprints_index() -> str:
        res = await ctx.dispatcher.call(
            "unreal_search_assets", {"class_name": "Blueprint", "limit": 100}
        )
        return json.dumps(res, indent=2)

    @mcp.resource("unreal://materials/index")
    async def materials_index() -> str:
        res = await ctx.dispatcher.call(
            "unreal_search_assets", {"class_name": "Material", "limit": 100}
        )
        return json.dumps(res, indent=2)

    @mcp.resource("unreal://logs/recent")
    async def logs_recent() -> str:
        res = await ctx.dispatcher.call("unreal_get_logs", {"limit": 100})
        return json.dumps(res, indent=2)
