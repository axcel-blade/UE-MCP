"""Tool package auto-registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register_all_tools(mcp: FastMCP, ctx: AppContext) -> None:
    from mcp_server.tools.actors import tools as actors_tools
    from mcp_server.tools.animation import tools as animation_tools
    from mcp_server.tools.assets import tools as assets_tools
    from mcp_server.tools.blueprints import tools as blueprints_tools
    from mcp_server.tools.gameplay import tools as gameplay_tools
    from mcp_server.tools.industries import tools as industries_tools
    from mcp_server.tools.intelligence import tools as intelligence_tools
    from mcp_server.tools.levels import tools as levels_tools
    from mcp_server.tools.lighting import tools as lighting_tools
    from mcp_server.tools.materials import tools as materials_tools
    from mcp_server.tools.meshes import tools as meshes_tools
    from mcp_server.tools.niagara import tools as niagara_tools
    from mcp_server.tools.online_assets import tools as online_assets_tools
    from mcp_server.tools.physics import tools as physics_tools
    from mcp_server.tools.pipeline import tools as pipeline_tools
    from mcp_server.tools.production import tools as production_tools
    from mcp_server.tools.project import tools as project_tools
    from mcp_server.tools.rendering import tools as rendering_tools
    from mcp_server.tools.scripting import tools as scripting_tools
    from mcp_server.tools.sequencer import tools as sequencer_tools
    from mcp_server.tools.system import tools as system_tools
    from mcp_server.tools.testing import tools as testing_tools
    from mcp_server.tools.widgets import tools as widgets_tools
    from mcp_server.tools.workflows import tools as workflows_tools

    system_tools.register(mcp, ctx)
    actors_tools.register(mcp, ctx)
    levels_tools.register(mcp, ctx)
    blueprints_tools.register(mcp, ctx)
    assets_tools.register(mcp, ctx)
    materials_tools.register(mcp, ctx)
    lighting_tools.register(mcp, ctx)
    meshes_tools.register(mcp, ctx)
    animation_tools.register(mcp, ctx)
    niagara_tools.register(mcp, ctx)
    widgets_tools.register(mcp, ctx)
    sequencer_tools.register(mcp, ctx)
    rendering_tools.register(mcp, ctx)
    physics_tools.register(mcp, ctx)
    gameplay_tools.register(mcp, ctx)
    project_tools.register(mcp, ctx)
    testing_tools.register(mcp, ctx)
    intelligence_tools.register(mcp, ctx)
    pipeline_tools.register(mcp, ctx)
    workflows_tools.register(mcp, ctx)
    scripting_tools.register(mcp, ctx)
    industries_tools.register(mcp, ctx)
    online_assets_tools.register(mcp, ctx)
    production_tools.register(mcp, ctx)
