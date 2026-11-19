"""High-level workflows composed from lower-level tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(name="unreal_create_room")
    async def unreal_create_room(
        width: float = 400.0,
        length: float = 400.0,
        height: float = 300.0,
        wall_thickness: float = 10.0,
        name_prefix: str = "MCP_Room",
        **params: Any,
    ) -> dict[str, Any]:
        """Create a simple room using scaled cube actors."""
        steps = []
        half_w, half_l, half_h = width / 2, length / 2, height / 2
        specs = [
            (f"{name_prefix}_Floor", (0, 0, 0), (width / 100, length / 100, wall_thickness / 100)),
            (
                f"{name_prefix}_Ceiling",
                (0, 0, height),
                (width / 100, length / 100, wall_thickness / 100),
            ),
            (
                f"{name_prefix}_Wall_N",
                (0, half_l, half_h),
                (width / 100, wall_thickness / 100, height / 100),
            ),
            (
                f"{name_prefix}_Wall_S",
                (0, -half_l, half_h),
                (width / 100, wall_thickness / 100, height / 100),
            ),
            (
                f"{name_prefix}_Wall_E",
                (half_w, 0, half_h),
                (wall_thickness / 100, length / 100, height / 100),
            ),
            (
                f"{name_prefix}_Wall_W",
                (-half_w, 0, half_h),
                (wall_thickness / 100, length / 100, height / 100),
            ),
        ]
        created = []
        for label, loc, scale in specs:
            res = await ctx.dispatcher.call(
                "unreal_spawn_actor",
                {
                    "class_name": "StaticMeshActor",
                    "name": label,
                    "location": {"x": loc[0], "y": loc[1], "z": loc[2]},
                    "scale": {"x": scale[0], "y": scale[1], "z": scale[2]},
                    "mesh": "/Engine/BasicShapes/Cube.Cube",
                },
            )
            steps.append(res)
            if res.get("success"):
                created.append(label)
            else:
                return {
                    "success": False,
                    "error": res.get("error"),
                    "partial": created,
                    "steps": steps,
                }
        return {
            "success": True,
            "result": {
                "created": created,
                "dimensions": {"width": width, "length": length, "height": height},
            },
            "steps": steps,
        }

    @mcp.tool(name="unreal_setup_lighting")
    async def unreal_setup_lighting(
        include_sky: bool = True,
        include_fog: bool = False,
        directional_intensity: float = 10.0,
        **params: Any,
    ) -> dict[str, Any]:
        """Set up a basic lighting environment."""
        steps = []
        sun = await ctx.dispatcher.call(
            "unreal_create_directional_light",
            {
                "name": "MCP_Sun",
                "location": {"x": 0, "y": 0, "z": 500},
                "rotation": {"pitch": -40, "yaw": 45, "roll": 0},
                "intensity": directional_intensity,
            },
        )
        steps.append(sun)
        if include_sky:
            steps.append(
                await ctx.dispatcher.call("unreal_create_sky_light", {"name": "MCP_SkyLight"})
            )
            steps.append(
                await ctx.dispatcher.call(
                    "unreal_create_sky_atmosphere", {"name": "MCP_SkyAtmosphere"}
                )
            )
        if include_fog:
            steps.append(
                await ctx.dispatcher.call(
                    "unreal_create_exponential_height_fog", {"name": "MCP_HeightFog"}
                )
            )
        ok = all(s.get("success") for s in steps)
        return {"success": ok, "result": {"steps": len(steps)}, "steps": steps}

    @mcp.tool(name="unreal_setup_camera")
    async def unreal_setup_camera(
        name: str = "MCP_Camera",
        location: dict[str, float] | None = None,
        rotation: dict[str, float] | None = None,
        **params: Any,
    ) -> dict[str, Any]:
        """Create and configure a cinematic camera actor."""
        loc = location or {"x": 0, "y": -500, "z": 200}
        rot = rotation or {"pitch": -10, "yaw": 0, "roll": 0}
        spawn = await ctx.dispatcher.call(
            "unreal_spawn_actor",
            {"class_name": "CameraActor", "name": name, "location": loc, "rotation": rot},
        )
        if not spawn.get("success"):
            return spawn
        view = await ctx.dispatcher.call(
            "unreal_set_viewport_location",
            {"x": loc["x"], "y": loc["y"], "z": loc["z"]},
        )
        return {"success": True, "result": {"camera": name, "viewport": view}}

    @mcp.tool(name="unreal_build_scene")
    async def unreal_build_scene(
        spec: dict[str, Any] | None = None, **params: Any
    ) -> dict[str, Any]:
        """Build a scene from a structured specification of actors/lights."""
        spec = spec or params.get("specification") or {}
        steps = []
        for actor in spec.get("actors", []):
            steps.append(await ctx.dispatcher.call("unreal_spawn_actor", actor))
        if spec.get("lighting"):
            steps.append(await unreal_setup_lighting(**spec["lighting"]))
        if spec.get("camera"):
            steps.append(await unreal_setup_camera(**spec["camera"]))
        ok = all(s.get("success") for s in steps) if steps else True
        return {"success": ok, "result": {"operations": len(steps)}, "steps": steps}

    @mcp.tool(name="unreal_create_gameplay_prototype")
    async def unreal_create_gameplay_prototype(
        blueprint_path: str = "/Game/MCP/BP_MCPPrototype",
        parent_class: str = "Actor",
        **params: Any,
    ) -> dict[str, Any]:
        """Create a minimal Blueprint gameplay prototype scaffold."""
        created = await ctx.dispatcher.call(
            "unreal_create_blueprint",
            {"path": blueprint_path, "parent_class": parent_class},
        )
        if not created.get("success"):
            return created
        compiled = await ctx.dispatcher.call("unreal_compile_blueprint", {"path": blueprint_path})
        saved = await ctx.dispatcher.call("unreal_save_blueprint", {"path": blueprint_path})
        return {
            "success": compiled.get("success") and saved.get("success"),
            "result": {"blueprint": blueprint_path},
            "steps": [created, compiled, saved],
        }

    @mcp.tool(name="unreal_optimize_scene")
    async def unreal_optimize_scene(**params: Any) -> dict[str, Any]:
        """Analyze scene performance and recommend optimization actions."""
        stats = await ctx.dispatcher.call("unreal_get_scene_statistics", {})
        actors = await ctx.dispatcher.call("unreal_get_all_actors", {"limit": 500})
        recommendations = []
        if stats.get("success"):
            result = stats.get("result") or {}
            count = result.get("actor_count") or result.get("num_actors")
            if isinstance(count, int) and count > 500:
                recommendations.append("High actor count; consider HLOD or world partition.")
            if result.get("dynamic_lights", 0) > 4:
                recommendations.append("Reduce movable lights or bake lighting.")
        return {
            "success": True,
            "result": {"recommendations": recommendations, "stats": stats, "actors_sample": actors},
        }

    @mcp.tool(name="unreal_validate_project")
    async def unreal_validate_project(**params: Any) -> dict[str, Any]:
        """Perform a comprehensive project validation."""
        steps = [
            await ctx.dispatcher.call("unreal_get_project_diagnostics", {}),
            await ctx.dispatcher.call("unreal_validate_assets", {"path": "/Game", "limit": 100}),
            await ctx.dispatcher.call("unreal_validate_blueprints", {"path": "/Game", "limit": 50}),
            await ctx.dispatcher.call(
                "unreal_find_missing_references", {"path": "/Game", "limit": 50}
            ),
        ]
        ok = all(s.get("success") for s in steps)
        return {"success": ok, "result": {"checks": len(steps)}, "steps": steps}
