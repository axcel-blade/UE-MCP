"""Production tool pack.

Template tools run vetted editor-Python through the shared ``compose`` wrapper (one
undo step, spawned actors cleaned up on failure) and verify their own results inside
the editor before returning. File-system tools (C++ scaffolding, plugins, logs, build)
run server-side against the project the connected editor reports, so they never guess
paths. Every tool goes through the configured permission gates.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp_server.core.permissions import assert_tool_allowed
from mcp_server.core.python_exec import run_python
from mcp_server.core.response import fail, ok
from mcp_server.exceptions import UnrealEngineMCPError
from mcp_server.tools.industries.tools import compose
from mcp_server.tools.production import cpp_templates

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext

# Extra helpers for this pack, appended after the shared prelude.
HELPERS = r"""
import random

def load_mesh(mesh):
    sm = unreal.load_asset(SHAPES.get(mesh, mesh))
    if not isinstance(sm, unreal.StaticMesh):
        raise ValueError("Static mesh not found: %s" % mesh)
    return sm

def place(label, mesh, loc, rot=None, scale=None, material=None, folder=None):
    a = spawn_mesh(label, mesh, loc, rot, scale, material)
    if folder:
        a.set_folder_path(folder)
    return a

def need(name, plugin):
    if not has(name):
        raise RuntimeError("unreal.%s is unavailable; enable the %s plugin and restart the editor" % (name, plugin))
    return getattr(unreal, name)
"""

_BUILD_ERR = re.compile(
    r"(?P<file>[^\s(][^(]*)\((?P<line>\d+)[^)]*\)\s*:\s*(?P<sev>error|warning)\s*(?P<msg>.*)"
)


def register(mcp: FastMCP, ctx: AppContext) -> None:
    def gate(name: str, confirmed: bool = False) -> dict[str, Any] | None:
        try:
            assert_tool_allowed(ctx.settings, name, confirmed=confirmed)
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        return None

    async def run(
        tool: str,
        body: str,
        /,
        *,
        confirmed: bool = False,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        denied = gate(tool, confirmed)
        if denied:
            return denied
        label = kwargs.pop("_undo", "Unreal MCP")
        return await run_python(ctx, compose(HELPERS + body, label, **kwargs), timeout=timeout)

    async def project_paths() -> dict[str, Any]:
        """Ask the editor where its project and engine live (never guessed)."""
        res = await run_python(
            ctx,
            "result = {'project_file': unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path()),"
            " 'project_dir': unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),"
            " 'engine_dir': unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir()),"
            " 'log_dir': unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_log_dir()),"
            " 'name': unreal.SystemLibrary.get_game_name()}",
        )
        if not res.get("success"):
            raise UnrealEngineMCPError(
                "Could not read project paths from the editor: "
                + str(res.get("error", {}).get("message", "unknown error")),
                code="not_connected",
            )
        return res["result"]["result"]

    # =============================================================================
    # PROCEDURAL PLACEMENT & CONSTRUCTION
    # =============================================================================

    @mcp.tool(name="unreal_spawn_actor_pattern")
    async def unreal_spawn_actor_pattern(
        pattern: str,
        mesh: str = "cube",
        count: int = 10,
        origin: dict[str, float] | None = None,
        spacing: float = 200.0,
        columns: int = 0,
        radius: float = 1000.0,
        extent: dict[str, float] | None = None,
        path_points: list[dict[str, float]] | None = None,
        scale_range: list[float] | None = None,
        random_yaw: bool = False,
        min_distance: float = 0.0,
        seed: int = 0,
        label_prefix: str = "Pattern",
        folder: str = "MCP/Patterns",
        material: str = "",
    ) -> dict[str, Any]:
        """Spawn ``count`` static-mesh actors in a pattern and verify they exist.

        pattern: "grid" (``columns``, ``spacing``), "line" (``spacing`` along +X),
        "circle" (``radius``), "random_region" (uniform inside ``extent`` half-size,
        optional ``min_distance`` rejection), or "path" (evenly along ``path_points``).
        ``mesh`` is a basic shape (cube/sphere/cylinder/cone/plane) or a StaticMesh path.
        ``scale_range`` [min,max] randomises uniform scale; ``seed`` makes runs repeatable.
        """
        if not 1 <= count <= 5000:
            return fail("count must be between 1 and 5000", code="invalid_params")
        return await run(
            "unreal_spawn_actor_pattern",
            """
rng = random.Random(ARGS["seed"])
o = V(ARGS["origin"])
n = ARGS["count"]; pat = ARGS["pattern"]
pts = []
if pat == "grid":
    cols = ARGS["columns"] or max(1, int(math.ceil(math.sqrt(n))))
    for i in range(n):
        pts.append(unreal.Vector(o.x + (i % cols) * ARGS["spacing"], o.y + (i // cols) * ARGS["spacing"], o.z))
elif pat == "line":
    pts = [unreal.Vector(o.x + i * ARGS["spacing"], o.y, o.z) for i in range(n)]
elif pat == "circle":
    r = ARGS["radius"]
    pts = [unreal.Vector(o.x + r * math.cos(2 * math.pi * i / n), o.y + r * math.sin(2 * math.pi * i / n), o.z) for i in range(n)]
elif pat == "random_region":
    e = V(ARGS["extent"], (2000, 2000, 0)); md = ARGS["min_distance"]; tries = 0
    while len(pts) < n and tries < n * 50:
        tries += 1
        p = unreal.Vector(o.x + rng.uniform(-e.x, e.x), o.y + rng.uniform(-e.y, e.y), o.z + rng.uniform(-e.z, e.z))
        if md <= 0 or all((p - q).length() >= md for q in pts):
            pts.append(p)
    if len(pts) < n:
        raise ValueError("Only %d of %d points fit with min_distance=%s; enlarge extent or lower count" % (len(pts), n, md))
elif pat == "path":
    path = [V(p) for p in (ARGS["path_points"] or [])]
    if len(path) < 2:
        raise ValueError("pattern=path needs at least 2 path_points")
    segs = [(path[i], path[i + 1], (path[i + 1] - path[i]).length()) for i in range(len(path) - 1)]
    total = sum(s[2] for s in segs)
    for i in range(n):
        d = total * i / max(1, n - 1)
        for a, b, L in segs:
            if d <= L or (a, b, L) == segs[-1]:
                t = 0 if L == 0 else min(1.0, d / L)
                pts.append(unreal.Vector(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t))
                break
            d -= L
else:
    raise ValueError("pattern must be grid, line, circle, random_region or path")
load_mesh(ARGS["mesh"])
labels = []
for i, p in enumerate(pts):
    sr = ARGS["scale_range"]
    s = rng.uniform(sr[0], sr[1]) if sr else None
    yaw = rng.uniform(0, 360) if ARGS["random_yaw"] else 0
    a = place("%s_%03d" % (ARGS["label_prefix"], i), ARGS["mesh"], p, (0, yaw, 0), s, ARGS["material"] or None, ARGS["folder"])
    labels.append(a.get_actor_label())
present = {x.get_actor_label() for x in EAS.get_all_level_actors()}
missing = [l for l in labels if l not in present]
if missing:
    raise RuntimeError("Spawn verification failed for %d actors" % len(missing))
result = {"spawned": len(labels), "verified": True, "labels": labels[:50], "folder": ARGS["folder"]}
""",
            pattern=pattern,
            mesh=mesh,
            count=count,
            origin=origin,
            spacing=spacing,
            columns=columns,
            radius=radius,
            extent=extent,
            path_points=path_points,
            scale_range=scale_range,
            random_yaw=random_yaw,
            min_distance=min_distance,
            seed=seed,
            label_prefix=label_prefix,
            folder=folder,
            material=material,
            _undo="Spawn actor pattern",
        )

    @mcp.tool(name="unreal_build_structure")
    async def unreal_build_structure(
        kind: str,
        name: str,
        origin: dict[str, float] | None = None,
        yaw: float = 0.0,
        length: float = 1000.0,
        width: float = 800.0,
        height: float = 300.0,
        thickness: float = 20.0,
        steps: int = 12,
        floors: int = 1,
        door_width: float = 120.0,
        post_spacing: float = 200.0,
        material: str = "",
    ) -> dict[str, Any]:
        """Construct architecture from scaled cube primitives, grouped in an outliner
        folder named ``name`` and verified after placement.

        kind: "wall" (length x height), "fence" (posts every ``post_spacing`` + rails),
        "floor" (length x width slab), "staircase" (``steps`` treads rising ``height``),
        "room" (floor + 4 walls with a door gap of ``door_width`` in the front wall),
        "building" (``floors`` stacked rooms with ceilings), "tower" (cylinder + crenels).
        Units are cm. Use your project's modular meshes instead when they exist.
        """
        return await run(
            "unreal_build_structure",
            """
o = V(ARGS["origin"]); yaw = ARGS["yaw"]; folder = "MCP/" + ARGS["name"]
L, W, H, T = ARGS["length"], ARGS["width"], ARGS["height"], ARGS["thickness"]
cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
mat = ARGS["material"] or None
parts = []
def box(tag, cx, cyy, cz, sx, sy_, sz, mesh="cube"):
    # Local (cx, cyy) rotated by yaw around origin; basic cube is 100 cm.
    wx = o.x + cx * cy - cyy * sy; wy = o.y + cx * sy + cyy * cy
    a = place("%s_%s_%02d" % (ARGS["name"], tag, len(parts)), mesh, (wx, wy, o.z + cz), (0, yaw, 0), (sx / 100.0, sy_ / 100.0, sz / 100.0), mat, folder)
    parts.append(a.get_actor_label())
def wall(x0, y0, x1, y1, z0, h, gap=0.0):
    dx, dy = x1 - x0, y1 - y0; ln = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dy, dx))
    segs = [(0.0, ln)] if gap <= 0 or gap >= ln else [(0.0, (ln - gap) / 2), ((ln + gap) / 2, ln)]
    for s0, s1 in segs:
        m = (s0 + s1) / 2; seg = s1 - s0
        cx = x0 + dx / ln * m; cyy = y0 + dy / ln * m
        wx = o.x + cx * cy - cyy * sy; wy = o.y + cx * sy + cyy * cy
        a = place("%s_Wall_%02d" % (ARGS["name"], len(parts)), "cube", (wx, wy, o.z + z0 + h / 2), (0, yaw + ang, 0), (seg / 100.0, T / 100.0, h / 100.0), mat, folder)
        parts.append(a.get_actor_label())
    if gap > 0 and gap < ln and h > 220:
        cx = x0 + dx / 2; cyy = y0 + dy / 2
        wx = o.x + cx * cy - cyy * sy; wy = o.y + cx * sy + cyy * cy
        a = place("%s_Lintel_%02d" % (ARGS["name"], len(parts)), "cube", (wx, wy, o.z + z0 + 220 + (h - 220) / 2), (0, yaw + ang, 0), (gap / 100.0, T / 100.0, (h - 220) / 100.0), mat, folder)
        parts.append(a.get_actor_label())
def room(z0, door=True):
    box("Floor", 0, 0, z0 + T / 2, L, W, T)
    hl, hw = L / 2, W / 2
    wall(-hl, -hw, hl, -hw, z0 + T, H, ARGS["door_width"] if door else 0)
    wall(hl, -hw, hl, hw, z0 + T, H); wall(hl, hw, -hl, hw, z0 + T, H); wall(-hl, hw, -hl, -hw, z0 + T, H)
k = ARGS["kind"]
if k == "wall":
    wall(-L / 2, 0, L / 2, 0, 0, H)
elif k == "floor":
    box("Floor", 0, 0, T / 2, L, W, T)
elif k == "fence":
    n = max(2, int(L // ARGS["post_spacing"]) + 1)
    for i in range(n):
        box("Post", -L / 2 + i * L / (n - 1), 0, H / 2, 12, 12, H)
    for z in (H * 0.35, H * 0.8):
        box("Rail", 0, 0, z, L, 6, 10)
elif k == "staircase":
    n = max(1, ARGS["steps"]); rise = H / n; run_ = L / n
    for i in range(n):
        box("Step", -L / 2 + run_ * (i + 0.5), 0, rise * (i + 1) / 2, run_, W, rise * (i + 1))
elif k == "room":
    room(0)
elif k == "building":
    for f in range(max(1, ARGS["floors"])):
        room(f * (H + T), door=(f == 0))
    box("Roof", 0, 0, max(1, ARGS["floors"]) * (H + T) + T / 2, L + T, W + T, T)
elif k == "tower":
    box("Body", 0, 0, H / 2, W, W, H, "cylinder")
    for i in range(8):
        a_ = 2 * math.pi * i / 8
        box("Crenel", (W / 2 - 20) * math.cos(a_), (W / 2 - 20) * math.sin(a_), H + 40, 40, 40, 80)
else:
    raise ValueError("kind must be wall, fence, floor, staircase, room, building or tower")
present = {x.get_actor_label() for x in EAS.get_all_level_actors()}
if any(p not in present for p in parts):
    raise RuntimeError("Structure verification failed")
result = {"kind": k, "parts": len(parts), "folder": folder, "verified": True}
""",
            kind=kind,
            name=name,
            origin=origin,
            yaw=yaw,
            length=length,
            width=width,
            height=height,
            thickness=thickness,
            steps=steps,
            floors=floors,
            door_width=door_width,
            post_spacing=post_spacing,
            material=material,
            _undo="Build structure",
        )

    @mcp.tool(name="unreal_organize_actors")
    async def unreal_organize_actors(
        folder: str,
        labels: list[str] | None = None,
        label_contains: str = "",
        class_name: str = "",
    ) -> dict[str, Any]:
        """Move actors into an outliner folder (scene hierarchy organisation). Select by
        explicit ``labels``, a ``label_contains`` substring and/or ``class_name``."""
        if not (labels or label_contains or class_name):
            return fail("Give labels, label_contains or class_name", code="invalid_params")
        return await run(
            "unreal_organize_actors",
            """
want = set(ARGS["labels"] or [])
moved = []
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if want and lab not in want:
        continue
    if ARGS["label_contains"] and ARGS["label_contains"] not in lab:
        continue
    if ARGS["class_name"] and a.get_class().get_name() != ARGS["class_name"]:
        continue
    a.set_folder_path(ARGS["folder"]); moved.append(lab)
result = {"folder": ARGS["folder"], "moved": len(moved), "labels": moved[:100]}
""",
            folder=folder,
            labels=labels,
            label_contains=label_contains,
            class_name=class_name,
            _undo="Organize actors",
        )

    # =============================================================================
    # LEVELS
    # =============================================================================

    @mcp.tool(name="unreal_list_levels")
    async def unreal_list_levels(path: str = "/Game") -> dict[str, Any]:
        """List level (World) assets under ``path`` and report the current level."""
        return await run(
            "unreal_list_levels",
            """
ar = unreal.AssetRegistryHelpers.get_asset_registry()
flt = unreal.ARFilter(package_paths=[ARGS["path"]], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "World")])
maps = sorted(str(d.package_name) for d in ar.get_assets(flt))
w = world()
result = {"current": w.get_path_name().split(".")[0] if w else None, "levels": maps, "count": len(maps)}
""",
            path=path,
        )

    @mcp.tool(name="unreal_duplicate_level")
    async def unreal_duplicate_level(source: str, destination: str) -> dict[str, Any]:
        """Duplicate a level asset (e.g. "/Game/Maps/Main" -> "/Game/Maps/Main_Copy").
        Refuses to overwrite an existing asset."""
        return await run(
            "unreal_duplicate_level",
            """
if not EAL.does_asset_exist(ARGS["src"]):
    raise ValueError("Level not found: " + ARGS["src"])
if EAL.does_asset_exist(ARGS["dst"]):
    raise ValueError("Destination already exists: " + ARGS["dst"])
if EAL.duplicate_asset(ARGS["src"], ARGS["dst"]) is None or not EAL.does_asset_exist(ARGS["dst"]):
    raise RuntimeError("Duplicate failed")
result = {"source": ARGS["src"], "destination": ARGS["dst"], "verified": True}
""",
            src=source,
            dst=destination,
        )

    @mcp.tool(name="unreal_delete_level")
    async def unreal_delete_level(level: str, confirmed: bool = False) -> dict[str, Any]:
        """Delete a level asset. Destructive: requires ``confirmed=true``. Refuses to
        delete the level that is currently open."""
        return await run(
            "unreal_delete_level",
            """
w = world()
if w and w.get_path_name().split(".")[0] == ARGS["level"]:
    raise ValueError("Refusing to delete the open level; open another level first")
if not EAL.does_asset_exist(ARGS["level"]):
    raise ValueError("Level not found: " + ARGS["level"])
if not EAL.delete_asset(ARGS["level"]) or EAL.does_asset_exist(ARGS["level"]):
    raise RuntimeError("Delete failed (asset may be referenced or open)")
result = {"deleted": ARGS["level"], "verified": True}
""",
            confirmed=confirmed,
            level=level,
        )

    # =============================================================================
    # PCG
    # =============================================================================

    @mcp.tool(name="unreal_create_pcg_volume")
    async def unreal_create_pcg_volume(
        label: str,
        graph: str = "",
        create_graph_path: str = "",
        center: dict[str, float] | None = None,
        extent: dict[str, float] | None = None,
        seed: int = 42,
        generate: bool = True,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Place a PCGVolume using an existing PCG graph (``graph`` asset path) or a new
        empty graph created at ``create_graph_path``; set its seed and optionally
        generate. Requires the PCG plugin. Author graph nodes in the PCG editor or
        reuse graphs shipped with your project."""
        return await run(
            "unreal_create_pcg_volume",
            """
need("PCGVolume", "Procedural Content Generation Framework (PCG)")
if ARGS["graph"]:
    g = unreal.load_asset(ARGS["graph"])
    if g is None or g.get_class().get_name() != "PCGGraph":
        raise ValueError("PCG graph not found: " + ARGS["graph"])
elif ARGS["create_graph_path"]:
    g = new_asset(ARGS["create_graph_path"], need("PCGGraph", "PCG"), need("PCGGraphFactory", "PCG editor"))
    if g is None:
        raise RuntimeError("Could not create PCG graph")
    EAL.save_loaded_asset(g)
else:
    raise ValueError("Give graph or create_graph_path")
ext = V(ARGS["extent"], (2000, 2000, 500))
a = spawn(unreal.PCGVolume, ARGS["label"], ARGS["center"])
a.set_actor_scale3d(unreal.Vector(ext.x / 100.0, ext.y / 100.0, ext.z / 100.0))
comp = a.get_component_by_class(unreal.PCGComponent)
if comp is None:
    raise RuntimeError("PCGVolume has no PCGComponent")
comp.set_graph(g)
comp.set_editor_property("seed", int(ARGS["seed"]))
generated = False
if ARGS["generate"]:
    comp.generate(True); generated = True
result = {"label": a.get_actor_label(), "graph": g.get_path_name(), "seed": ARGS["seed"], "generate_requested": generated}
""",
            label=label,
            graph=graph,
            create_graph_path=create_graph_path,
            center=center,
            extent=extent,
            seed=seed,
            generate=generate,
            overwrite=overwrite,
            _undo="Create PCG volume",
        )

    @mcp.tool(name="unreal_generate_pcg")
    async def unreal_generate_pcg(
        label: str, seed: int | None = None, cleanup_only: bool = False
    ) -> dict[str, Any]:
        """Regenerate (or with ``cleanup_only`` delete generated content of) the PCG
        component on the actor ``label``, optionally changing its seed first."""
        return await run(
            "unreal_generate_pcg",
            """
need("PCGComponent", "PCG")
a = find(ARGS["label"])
comp = a.get_component_by_class(unreal.PCGComponent)
if comp is None:
    raise ValueError("Actor has no PCGComponent: " + ARGS["label"])
if ARGS["seed"] is not None:
    comp.set_editor_property("seed", int(ARGS["seed"]))
if ARGS["cleanup_only"]:
    comp.cleanup(True)
else:
    comp.generate(True)
result = {"label": ARGS["label"], "action": "cleanup" if ARGS["cleanup_only"] else "generate", "seed": comp.get_editor_property("seed")}
""",
            label=label,
            seed=seed,
            cleanup_only=cleanup_only,
            _undo="PCG generate",
        )

    # =============================================================================
    # LANDSCAPE / TERRAIN (Geometry Script dynamic mesh)
    # =============================================================================

    @mcp.tool(name="unreal_create_terrain_mesh")
    async def unreal_create_terrain_mesh(
        label: str = "Terrain",
        size: float = 20000.0,
        resolution: int = 128,
        height: float = 1500.0,
        frequency: float = 0.0003,
        octaves: int = 4,
        seed: int = 1,
        flatten_center_radius: float = 0.0,
        location: dict[str, float] | None = None,
        material: str = "",
    ) -> dict[str, Any]:
        """Generate a procedural heightfield terrain as a DynamicMeshActor (fractal
        value noise: hills/mountains via ``height``/``frequency``/``octaves``; optional
        flat plateau of ``flatten_center_radius`` for building sites), with collision.
        Requires the Geometry Script plugin. For sculptable Landscape actors, create
        them in Landscape mode; this tool is for fast blockout terrain."""
        if not 8 <= resolution <= 512:
            return fail("resolution must be between 8 and 512", code="invalid_params")
        return await run(
            "unreal_create_terrain_mesh",
            """
need("DynamicMeshActor", "Geometry Script")
GS = need("GeometryScript_Primitives", "Geometry Script")
rng = random.Random(ARGS["seed"])
N = ARGS["resolution"]; S = ARGS["size"]
lat = {}
def lattice(i, j, o):
    k = (i, j, o)
    if k not in lat:
        lat[k] = rng.random()
    return lat[k]
def vnoise(x, y, o):
    i, j = int(math.floor(x)), int(math.floor(y)); fx, fy = x - i, y - j
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a, b = lattice(i, j, o), lattice(i + 1, j, o); c, d = lattice(i, j + 1, o), lattice(i + 1, j + 1, o)
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy
def h(x, y):
    tot, amp, f, norm = 0.0, 1.0, ARGS["frequency"], 0.0
    for o in range(ARGS["octaves"]):
        tot += vnoise(x * f, y * f, o) * amp; norm += amp; amp *= 0.5; f *= 2
    z = tot / norm * ARGS["height"]
    r = ARGS["flatten_center_radius"]
    if r > 0:
        d = math.hypot(x, y)
        t = max(0.0, min(1.0, (d - r) / r))
        z = z * t
    return z
a = spawn(unreal.DynamicMeshActor, ARGS["label"], ARGS["location"])
dm = a.dynamic_mesh_component.get_dynamic_mesh()
opts = unreal.GeometryScriptPrimitiveOptions()
GS.append_rectangle_xy(dm, opts, unreal.Transform(), S, S, N, N)
pts = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(dm)[0] if hasattr(unreal, "GeometryScript_MeshQueries") else None
if pts is None:
    raise RuntimeError("Geometry Script mesh queries unavailable")
lst = unreal.GeometryScriptVectorList()
lst.set_editor_property("list", [unreal.Vector(p.x, p.y, h(p.x, p.y)) for p in pts.get_editor_property("list")])
unreal.GeometryScript_MeshBasicEditFunctions.set_all_mesh_vertex_positions(dm, lst)
unreal.GeometryScript_Normals.recompute_normals(dm, unreal.GeometryScriptCalculateNormalsOptions())
comp = a.dynamic_mesh_component
comp.set_editor_property("collision_type", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
comp.update_collision(False) if hasattr(comp, "update_collision") else None
if ARGS["material"]:
    m = unreal.load_asset(ARGS["material"])
    if m: comp.set_material(0, m)
vc = unreal.GeometryScript_MeshQueries.get_vertex_count(dm)
if vc <= 0:
    raise RuntimeError("Terrain mesh is empty")
result = {"label": a.get_actor_label(), "vertices": vc, "size_cm": S, "max_height_cm": ARGS["height"]}
""",
            label=label,
            size=size,
            resolution=resolution,
            height=height,
            frequency=frequency,
            octaves=octaves,
            seed=seed,
            flatten_center_radius=flatten_center_radius,
            location=location,
            material=material,
            timeout=300,
            _undo="Create terrain mesh",
        )

    # =============================================================================
    # AI
    # =============================================================================

    @mcp.tool(name="unreal_create_ai_assets")
    async def unreal_create_ai_assets(
        folder: str = "/Game/AI",
        name: str = "Enemy",
        blackboard_keys: dict[str, str] | None = None,
        create_controller: bool = True,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create a Blackboard (BB_<name>) with typed keys, a Behavior Tree (BT_<name>)
        bound to it, and optionally an AIController Blueprint (BP_<name>AIController).
        ``blackboard_keys`` maps key name -> type: bool, int, float, string, name,
        vector, rotator, object, class, enum. Author BT nodes in the Behavior Tree
        editor; this sets up the verified asset skeleton."""
        return await run(
            "unreal_create_ai_assets",
            """
types = {"bool": "BlackboardKeyType_Bool", "int": "BlackboardKeyType_Int", "float": "BlackboardKeyType_Float",
         "string": "BlackboardKeyType_String", "name": "BlackboardKeyType_Name", "vector": "BlackboardKeyType_Vector",
         "rotator": "BlackboardKeyType_Rotator", "object": "BlackboardKeyType_Object", "class": "BlackboardKeyType_Class",
         "enum": "BlackboardKeyType_Enum"}
keys = ARGS["keys"] or {"TargetActor": "object", "PatrolLocation": "vector", "HasLineOfSight": "bool"}
for k, t in keys.items():
    if t not in types:
        raise ValueError("Unknown blackboard key type '%s' for %s" % (t, k))
base = ARGS["folder"].rstrip("/") + "/"
bb = new_asset(base + "BB_" + ARGS["name"], unreal.BlackboardData, unreal.BlackboardDataFactory())
entries = []
for k, t in keys.items():
    e = unreal.BlackboardEntry()
    e.set_editor_property("entry_name", k)
    e.set_editor_property("key_type", unreal.new_object(getattr(unreal, types[t]), bb))
    entries.append(e)
bb.set_editor_property("keys", entries)
EAL.save_loaded_asset(bb)
bt = new_asset(base + "BT_" + ARGS["name"], unreal.BehaviorTree, unreal.BehaviorTreeFactory())
bt.set_editor_property("blackboard_asset", bb)
EAL.save_loaded_asset(bt)
out = {"blackboard": bb.get_path_name(), "behavior_tree": bt.get_path_name(),
       "keys": [str(e.get_editor_property("entry_name")) for e in bb.get_editor_property("keys")]}
if ARGS["controller"]:
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.AIController)
    bp = new_asset(base + "BP_" + ARGS["name"] + "AIController", unreal.Blueprint, f)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); EAL.save_loaded_asset(bp)
    out["ai_controller"] = bp.get_path_name()
result = out
""",
            folder=folder,
            name=name,
            keys=blackboard_keys,
            controller=create_controller,
            overwrite=overwrite,
        )

    # =============================================================================
    # AUDIO
    # =============================================================================

    @mcp.tool(name="unreal_create_sound_cue")
    async def unreal_create_sound_cue(
        path: str,
        sound_wave: str,
        volume: float = 1.0,
        pitch: float = 1.0,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create a SoundCue wrapping an imported SoundWave (import WAV/MP3 first with
        unreal_import_asset)."""
        return await run(
            "unreal_create_sound_cue",
            """
w = unreal.load_asset(ARGS["wave"])
if not isinstance(w, unreal.SoundWave):
    raise ValueError("SoundWave not found: " + ARGS["wave"])
f = unreal.SoundCueFactoryNew(); f.set_editor_property("initial_sound_wave", w)
cue = new_asset(ARGS["path"], unreal.SoundCue, f)
if cue is None:
    raise RuntimeError("Could not create SoundCue")
cue.set_editor_property("volume_multiplier", float(ARGS["volume"]))
cue.set_editor_property("pitch_multiplier", float(ARGS["pitch"]))
EAL.save_loaded_asset(cue)
result = {"sound_cue": cue.get_path_name(), "duration_s": round(cue.get_editor_property("duration"), 3)}
""",
            path=path,
            wave=sound_wave,
            volume=volume,
            pitch=pitch,
            overwrite=overwrite,
        )

    @mcp.tool(name="unreal_create_sound_attenuation")
    async def unreal_create_sound_attenuation(
        path: str,
        inner_radius: float = 400.0,
        falloff_distance: float = 3600.0,
        spatialize: bool = True,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create a SoundAttenuation asset (distance falloff + spatialization)."""
        return await run(
            "unreal_create_sound_attenuation",
            """
att = new_asset(ARGS["path"], unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
s = att.get_editor_property("attenuation")
s.set_editor_property("spatialize", bool(ARGS["spatialize"]))
s.set_editor_property("falloff_distance", float(ARGS["falloff"]))
shape = s.get_editor_property("attenuation_shape_extents")
s.set_editor_property("attenuation_shape_extents", unreal.Vector(float(ARGS["inner"]), shape.y, shape.z))
att.set_editor_property("attenuation", s)
EAL.save_loaded_asset(att)
result = {"attenuation": att.get_path_name(), "inner_radius": ARGS["inner"], "falloff": ARGS["falloff"]}
""",
            path=path,
            inner=inner_radius,
            falloff=falloff_distance,
            spatialize=spatialize,
            overwrite=overwrite,
        )

    @mcp.tool(name="unreal_spawn_ambient_sound")
    async def unreal_spawn_ambient_sound(
        sound: str,
        label: str = "AmbientSound",
        location: dict[str, float] | None = None,
        attenuation: str = "",
        volume: float = 1.0,
        auto_activate: bool = True,
    ) -> dict[str, Any]:
        """Place an AmbientSound actor playing ``sound`` (SoundWave/SoundCue/MetaSound
        source), with optional attenuation asset."""
        return await run(
            "unreal_spawn_ambient_sound",
            """
snd = unreal.load_asset(ARGS["sound"])
if not isinstance(snd, unreal.SoundBase):
    raise ValueError("Sound not found: " + ARGS["sound"])
a = spawn(unreal.AmbientSound, ARGS["label"], ARGS["location"])
c = a.get_editor_property("audio_component")
c.set_editor_property("sound", snd)
c.set_editor_property("volume_multiplier", float(ARGS["volume"]))
c.set_editor_property("auto_activate", bool(ARGS["auto"]))
if ARGS["att"]:
    at = unreal.load_asset(ARGS["att"])
    if not isinstance(at, unreal.SoundAttenuation):
        raise ValueError("SoundAttenuation not found: " + ARGS["att"])
    c.set_editor_property("attenuation_settings", at)
result = {"label": a.get_actor_label(), "sound": snd.get_path_name(), **loc_list(a)}
""",
            sound=sound,
            label=label,
            location=location,
            att=attenuation,
            volume=volume,
            auto=auto_activate,
            _undo="Spawn ambient sound",
        )

    # =============================================================================
    # NIAGARA
    # =============================================================================

    @mcp.tool(name="unreal_place_niagara_effect")
    async def unreal_place_niagara_effect(
        system: str,
        label: str = "VFX",
        location: dict[str, float] | None = None,
        rotation: dict[str, float] | None = None,
        scale: float = 1.0,
        user_parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Place a NiagaraActor for an existing Niagara system (fire, smoke, rain...;
        search your project/Marketplace content first) and set user parameters
        (float, bool, int, [r,g,b,a] colour or {x,y,z} vector)."""
        return await run(
            "unreal_place_niagara_effect",
            """
need("NiagaraActor", "Niagara")
sysa = unreal.load_asset(ARGS["system"])
if sysa is None or sysa.get_class().get_name() != "NiagaraSystem":
    raise ValueError("Niagara system not found: " + ARGS["system"])
a = spawn(unreal.NiagaraActor, ARGS["label"], ARGS["location"], ARGS["rotation"])
a.set_actor_scale3d(unreal.Vector(ARGS["scale"], ARGS["scale"], ARGS["scale"]))
c = a.niagara_component
c.set_asset(sysa)
applied = {}
for k, v in (ARGS["params"] or {}).items():
    if isinstance(v, bool):
        c.set_variable_bool(k, v)
    elif isinstance(v, int):
        c.set_variable_int(k, v)
    elif isinstance(v, float):
        c.set_variable_float(k, v)
    elif isinstance(v, list) and len(v) in (3, 4):
        c.set_variable_linear_color(k, unreal.LinearColor(*([float(x) for x in v] + [1.0])[:4]))
    elif isinstance(v, dict):
        c.set_variable_vec3(k, V(v))
    else:
        raise ValueError("Unsupported value for user parameter " + k)
    applied[k] = v
c.activate(True)
result = {"label": a.get_actor_label(), "system": sysa.get_path_name(), "parameters": applied}
""",
            system=system,
            label=label,
            location=location,
            rotation=rotation,
            scale=scale,
            params=user_parameters,
            _undo="Place Niagara effect",
        )

    # =============================================================================
    # PROJECT FILES: plugins, C++, logs, build
    # =============================================================================

    def _uproject(paths: dict[str, Any]) -> Path:
        p = Path(paths["project_file"])
        if not p.is_file():
            raise UnrealEngineMCPError(f"Project file not found: {p}", code="not_found")
        return p

    @mcp.tool(name="unreal_list_project_plugins")
    async def unreal_list_project_plugins() -> dict[str, Any]:
        """List plugins declared in the .uproject and plugins in the project's
        Plugins folder, with their enabled state."""
        if denied := gate("unreal_list_project_plugins"):
            return denied
        try:
            paths = await project_paths()
            data = json.loads(_uproject(paths).read_text(encoding="utf-8-sig"))
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        declared = {p["Name"]: bool(p.get("Enabled", False)) for p in data.get("Plugins", [])}
        local = sorted(
            f.stem for f in (Path(paths["project_dir"]) / "Plugins").glob("**/*.uplugin")
        )
        return ok(
            {
                "declared": declared,
                "project_plugins": local,
                "engine_association": data.get("EngineAssociation"),
            }
        )

    @mcp.tool(name="unreal_set_plugin_enabled")
    async def unreal_set_plugin_enabled(
        plugin: str, enabled: bool = True, confirmed: bool = False
    ) -> dict[str, Any]:
        """Enable/disable a plugin in the .uproject (takes effect after an editor
        restart). Writes a ``.uproject.bak`` backup first. Requires ``confirmed=true``."""
        if denied := gate("unreal_set_plugin_enabled", confirmed):
            return denied
        if not re.match(r"^[A-Za-z0-9_.-]+$", plugin):
            return fail("Invalid plugin name", code="invalid_params")
        try:
            path = _uproject(await project_paths())
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
        plugins = data.setdefault("Plugins", [])
        entry = next((p for p in plugins if p.get("Name") == plugin), None)
        previous = entry.get("Enabled") if entry else None
        if entry is None:
            plugins.append({"Name": plugin, "Enabled": enabled})
        else:
            entry["Enabled"] = enabled
        path.with_suffix(".uproject.bak").write_text(raw, encoding="utf-8")
        path.write_text(json.dumps(data, indent="\t") + "\n", encoding="utf-8")
        verify = json.loads(path.read_text(encoding="utf-8"))
        state = next(p["Enabled"] for p in verify["Plugins"] if p["Name"] == plugin)
        return ok(
            {
                "plugin": plugin,
                "enabled": state,
                "previous": previous,
                "backup": str(path.with_suffix(".uproject.bak")),
                "restart_required": True,
            }
        )

    @mcp.tool(name="unreal_create_cpp_class")
    async def unreal_create_cpp_class(
        name: str, kind: str = "actor", module: str = "", subfolder: str = ""
    ) -> dict[str, Any]:
        """Scaffold a C++ class (header + source) in the project's Source module using
        Unreal conventions (UCLASS, GENERATED_BODY, <MODULE>_API, Public/Private).

        kind: actor, pawn, character, actor_component, scene_component, game_mode,
        game_state, player_controller, player_state, hud, ai_controller, object,
        game_instance_subsystem, world_subsystem, blueprint_function_library, interface.
        Never overwrites existing files. Compile with unreal_build_project afterwards.
        """
        if denied := gate("unreal_create_cpp_class"):
            return denied
        if subfolder and not re.match(r"^[A-Za-z0-9_/]+$", subfolder):
            return fail(
                "subfolder may contain only letters, digits, _ and /", code="invalid_params"
            )
        try:
            paths = await project_paths()
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        source_root = Path(paths["project_dir"]) / "Source"
        mod = module or paths["name"]
        mod_dir = source_root / mod
        if not (mod_dir / f"{mod}.Build.cs").is_file():
            found = sorted(p.parent.name for p in source_root.glob("*/*.Build.cs"))
            return fail(
                f"Module '{mod}' not found under {source_root}. Available: {found or 'none'}"
                " (Blueprint-only projects need a first C++ class from the editor).",
                code="not_found",
            )
        try:
            base, header, source = cpp_templates.render(kind, name, mod)
        except ValueError as exc:
            return fail(str(exc), code="invalid_params")
        split = (mod_dir / "Public").is_dir() and (mod_dir / "Private").is_dir()
        hdir = (mod_dir / "Public" if split else mod_dir) / subfolder
        cdir = (mod_dir / "Private" if split else mod_dir) / subfolder
        h, c = hdir / f"{base}.h", cdir / f"{base}.cpp"
        if h.exists() or c.exists():
            return fail(
                f"Refusing to overwrite existing {h if h.exists() else c}", code="already_exists"
            )
        hdir.mkdir(parents=True, exist_ok=True)
        cdir.mkdir(parents=True, exist_ok=True)
        h.write_text(header, encoding="utf-8")
        c.write_text(source, encoding="utf-8")
        return ok(
            {
                "header": str(h),
                "source": str(c),
                "module": mod,
                "kind": kind,
                "verified": h.is_file() and c.is_file(),
                "next": "Run unreal_build_project (editor closed) or Live Coding.",
            }
        )

    @mcp.tool(name="unreal_get_output_log")
    async def unreal_get_output_log(
        lines: int = 200, severity: str = "", contains: str = ""
    ) -> dict[str, Any]:
        """Read the tail of the editor's project log (Saved/Logs/<Project>.log).
        ``severity``: "error", "warning" or "" for all; ``contains`` filters text."""
        if denied := gate("unreal_get_output_log"):
            return denied
        try:
            paths = await project_paths()
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        log = Path(paths["log_dir"]) / f"{paths['name']}.log"
        if not log.is_file():
            return fail(f"Log file not found: {log}", code="not_found")
        text = log.read_text(encoding="utf-8", errors="replace").splitlines()
        sev = severity.lower()
        out = [
            ln
            for ln in text
            if (not sev or f"{sev}:" in ln.lower())
            and (not contains or contains.lower() in ln.lower())
        ]
        tail = out[-max(1, min(lines, 5000)) :]
        return ok(
            {
                "log_file": str(log),
                "matched": len(out),
                "returned": len(tail),
                "errors": sum("error:" in ln.lower() for ln in text),
                "warnings": sum("warning:" in ln.lower() for ln in text),
                "lines": tail,
            }
        )

    @mcp.tool(name="unreal_build_project")
    async def unreal_build_project(
        configuration: str = "Development",
        target: str = "",
        platform: str = "",
        confirmed: bool = False,
        timeout_seconds: int = 1800,
    ) -> dict[str, Any]:
        """Compile the project's C++ with UnrealBuildTool (default target
        <Project>Editor). Close the editor first or use Live Coding, since UBT cannot
        replace DLLs the editor has loaded. Returns parsed errors/warnings.
        Restricted: advanced security mode and ``confirmed=true``."""
        if denied := gate("unreal_build_project", confirmed):
            return denied
        if configuration not in ("Debug", "DebugGame", "Development", "Shipping", "Test"):
            return fail("Invalid configuration", code="invalid_params")
        if target and not re.match(r"^[A-Za-z0-9_]+$", target):
            return fail("Invalid target", code="invalid_params")
        try:
            paths = await project_paths()
            uproject = _uproject(paths)
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        plat = platform or {"win32": "Win64", "darwin": "Mac"}.get(sys.platform, "Linux")
        engine = Path(paths["engine_dir"])
        script = (
            engine
            / "Build"
            / "BatchFiles"
            / (
                "Build.bat"
                if plat == "Win64"
                else ("Mac/Build.sh" if plat == "Mac" else "Linux/Build.sh")
            )
        )
        if not script.is_file():
            return fail(f"Build script not found: {script}", code="not_found")
        tgt = target or f"{paths['name']}Editor"
        cmd = [str(script), tgt, plat, configuration, f"-Project={uproject}", "-WaitMutex"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )
            raw, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except TimeoutError:
            proc.kill()
            return fail(f"Build timed out after {timeout_seconds}s", code="timeout")
        out = raw.decode("utf-8", errors="replace").splitlines()
        diags = []
        for ln in out:
            m = _BUILD_ERR.search(ln)
            if m:
                diags.append(
                    {
                        "severity": m["sev"],
                        "file": m["file"].strip(),
                        "line": int(m["line"]),
                        "message": m["msg"].strip(),
                    }
                )
        errors = [d for d in diags if d["severity"] == "error"]
        data = {
            "command": cmd,
            "exit_code": proc.returncode,
            "errors": errors[:200],
            "warnings": [d for d in diags if d["severity"] == "warning"][:200],
            "tail": out[-60:],
        }
        if proc.returncode != 0:
            return fail(
                f"Build failed (exit {proc.returncode}, {len(errors)} errors)",
                code="build_failed",
                details=data,
            )
        return ok(data)
