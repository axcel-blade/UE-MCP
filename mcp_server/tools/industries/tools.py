"""Industry tool packs: games, film/video, live events & virtual production,
automotive/product design & manufacturing visualisation, and simulation.

Every tool here runs a vetted editor-Python template through ``run_python``, so the
packs work without enabling arbitrary script execution. Arguments are embedded with
``repr``/JSON, never string-formatted into code. Each template wraps its edits in an
undoable ``ScopedEditorTransaction``.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp_server.core.python_exec import run_python
from mcp_server.core.response import fail, ok
from mcp_server.exceptions import UnrealEngineMCPError

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext

# Shared helpers available to every template.
PRELUDE = r"""
import json, math
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
SHAPES = {"cube": "/Engine/BasicShapes/Cube.Cube", "sphere": "/Engine/BasicShapes/Sphere.Sphere",
          "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder", "cone": "/Engine/BasicShapes/Cone.Cone",
          "plane": "/Engine/BasicShapes/Plane.Plane"}

def V(v, d=(0.0, 0.0, 0.0)):
    v = v if v is not None else d
    if isinstance(v, unreal.Vector):
        return v
    if isinstance(v, dict):
        return unreal.Vector(float(v.get("x", 0)), float(v.get("y", 0)), float(v.get("z", 0)))
    return unreal.Vector(float(v[0]), float(v[1]), float(v[2]))

def R(r, d=(0.0, 0.0, 0.0)):
    r = r if r is not None else d
    if isinstance(r, unreal.Rotator):
        return r
    if isinstance(r, dict):
        return unreal.Rotator(roll=float(r.get("roll", 0)), pitch=float(r.get("pitch", 0)), yaw=float(r.get("yaw", 0)))
    return unreal.Rotator(roll=float(r[2]), pitch=float(r[0]), yaw=float(r[1]))

def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label or a.get_name() == label:
            return a
    raise ValueError("Actor not found: %s" % label)

def world():
    return UES.get_editor_world()

SPAWNED = []  # actors created by this call; destroyed again if the call fails

def _spawned(a, what):
    if a is not None:
        SPAWNED.append(a)
    if a is None:
        if LES.is_in_play_in_editor():
            raise RuntimeError("Cannot edit the level while Play/Simulate is running; call unreal_stop_play")
        raise RuntimeError("Unreal refused to spawn " + what)
    return a

def spawn_mesh(label, mesh="cube", loc=None, rot=None, scale=None, material=None):
    sm = unreal.load_asset(SHAPES.get(mesh, mesh))
    if not isinstance(sm, unreal.StaticMesh):
        raise ValueError("Static mesh not found: %s" % mesh)
    a = _spawned(EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(loc), R(rot)), label)
    a.set_actor_label(label)
    a.static_mesh_component.set_static_mesh(sm)
    if scale is not None:
        a.set_actor_scale3d(V(scale) if not isinstance(scale, (int, float)) else unreal.Vector(scale, scale, scale))
    if material:
        m = unreal.load_asset(material)
        if m:
            a.static_mesh_component.set_material(0, m)
    return a

def spawn(cls, label, loc=None, rot=None):
    a = _spawned(EAS.spawn_actor_from_class(cls, V(loc), R(rot)), label)
    a.set_actor_label(label)
    return a

def ensure_dir(path):
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)

def split(path):
    pkg = path.rsplit(".", 1)[0]
    return pkg.rsplit("/", 1)[0], pkg.rsplit("/", 1)[1]

def new_asset(path, cls, factory):
    folder, name = split(path)
    ensure_dir(folder)
    full = folder + "/" + name
    if EAL.does_asset_exist(full):
        if not ARGS.get("overwrite"):
            raise ValueError("Asset already exists: %s (pass overwrite=true to replace it)" % full)
        if not EAL.delete_asset(full):
            raise RuntimeError("Could not replace %s; close any editor that has it open" % full)
    return AT.create_asset(name, folder, cls, factory)

def loc_list(a):
    l = a.get_actor_location(); r = a.get_actor_rotation()
    return {"location": [round(l.x, 2), round(l.y, 2), round(l.z, 2)],
            "rotation": [round(r.pitch, 2), round(r.yaw, 2), round(r.roll, 2)]}

def has(name):
    return hasattr(unreal, name)
"""


def _args(**kwargs: Any) -> str:
    """Embed tool arguments into a template as a decoded JSON literal."""
    return f"ARGS = json.loads({json.dumps(json.dumps(kwargs))})\n"


def register(mcp: FastMCP, ctx: AppContext) -> None:
    async def run(body: str, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        label = kwargs.pop("_undo", "Unreal MCP")
        indented = "\n".join("    " + line for line in body.strip("\n").splitlines())
        # All-or-nothing for actors: if the template fails, destroy every actor it
        # spawned so a retry starts clean. Edits are one undo step on success.
        # (Asset creation is not undoable; templates validate inputs before creating
        # assets.)
        code = (
            PRELUDE
            + _args(**kwargs)
            + f"_txn = unreal.ScopedEditorTransaction({label!r})\n"
            + "try:\n"
            + indented
            + "\nexcept BaseException:\n"
            + "    for _a in reversed(SPAWNED):\n"
            + "        try:\n"
            + "            EAS.destroy_actor(_a)\n"
            + "        except Exception:\n"
            + "            pass\n"
            + "    raise\n"
            + "finally:\n"
            + "    del _txn\n"
        )
        return await run_python(ctx, code, timeout=timeout)

    # =============================================================================
    # GAMES
    # =============================================================================

    @mcp.tool(name="unreal_create_game_mode")
    async def unreal_create_game_mode(
        path: str = "/Game/Gameplay/BP_GameMode",
        default_pawn_class: str = "",
        player_controller_class: str = "",
        set_as_world_default: bool = True,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create a GameModeBase Blueprint, optionally set its default pawn / player
        controller (class paths like "/Script/Engine.DefaultPawn" or
        "/Game/BP_Hero.BP_Hero_C"), and make it this level's game mode override. ``overwrite`` replaces an existing asset at the same path."""
        return await run(
            """
f = unreal.BlueprintFactory()
f.set_editor_property("parent_class", unreal.GameModeBase)
bp = new_asset(ARGS["path"], unreal.Blueprint, f)
cls = unreal.load_object(None, bp.get_path_name() + "_C")
cdo = unreal.get_default_object(cls)
if ARGS["default_pawn_class"]:
    cdo.set_editor_property("default_pawn_class", unreal.load_class(None, ARGS["default_pawn_class"]))
if ARGS["player_controller_class"]:
    cdo.set_editor_property("player_controller_class", unreal.load_class(None, ARGS["player_controller_class"]))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
EAL.save_loaded_asset(bp)
if ARGS["set_as_world_default"]:
    world().get_world_settings().set_editor_property("default_game_mode", cls)
pawn = cdo.get_editor_property("default_pawn_class")
result = {"game_mode": bp.get_path_name(), "pawn": pawn.get_name() if pawn else None,
          "world_default": ARGS["set_as_world_default"]}
""",
            path=path,
            default_pawn_class=default_pawn_class,
            player_controller_class=player_controller_class,
            set_as_world_default=set_as_world_default,
            overwrite=overwrite,
            _undo="Create game mode",
        )

    @mcp.tool(name="unreal_set_world_game_mode")
    async def unreal_set_world_game_mode(game_mode_class: str) -> dict[str, Any]:
        """Set this level's GameMode override (World Settings). Class path, e.g.
        "/Game/Gameplay/BP_GameMode.BP_GameMode_C" or "/Script/Engine.GameModeBase"."""
        return await run(
            """
cls = unreal.load_class(None, ARGS["cls"])
if cls is None:
    raise ValueError("Class not found: " + ARGS["cls"])
world().get_world_settings().set_editor_property("default_game_mode", cls)
result = {"default_game_mode": cls.get_path_name()}
""",
            cls=game_mode_class,
            _undo="Set game mode",
        )

    @mcp.tool(name="unreal_add_player_start")
    async def unreal_add_player_start(
        location: dict[str, float] | None = None,
        yaw: float = 0.0,
        label: str = "PlayerStart",
    ) -> dict[str, Any]:
        """Place a PlayerStart (where the player spawns in PIE / packaged games)."""
        return await run(
            """
a = spawn(unreal.PlayerStart, ARGS["label"], ARGS["location"] or (0, 0, 100), (0, ARGS["yaw"], 0))
result = {"label": a.get_actor_label(), **loc_list(a)}
""",
            location=location,
            yaw=yaw,
            label=label,
            _undo="Add player start",
        )

    @mcp.tool(name="unreal_add_nav_mesh_volume")
    async def unreal_add_nav_mesh_volume(
        center: dict[str, float] | None = None,
        extent: dict[str, float] | None = None,
        label: str = "NavMeshBounds",
    ) -> dict[str, Any]:
        """Add a NavMeshBoundsVolume (AI navigation area) sized to ``extent`` (half
        size, cm) and rebuild navigation."""
        return await run(
            """
ext = V(ARGS["extent"], (2000, 2000, 500))
a = spawn(unreal.NavMeshBoundsVolume, ARGS["label"], ARGS["center"] or (0, 0, 0))
# The default brush is a 200 cm cube, so scale = extent / 100.
a.set_actor_scale3d(unreal.Vector(ext.x / 100.0, ext.y / 100.0, ext.z / 100.0))
unreal.SystemLibrary.execute_console_command(world(), "RebuildNavigation")
result = {"label": a.get_actor_label(), "extent_cm": [ext.x, ext.y, ext.z]}
""",
            center=center,
            extent=extent,
            label=label,
            _undo="Add nav mesh volume",
        )

    @mcp.tool(name="unreal_add_trigger_volume")
    async def unreal_add_trigger_volume(
        label: str,
        location: dict[str, float] | None = None,
        extent: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Add a TriggerBox (overlap events for gameplay scripting). ``extent`` is the
        half size in cm."""
        return await run(
            """
a = spawn(unreal.TriggerBox, ARGS["label"], ARGS["location"])
ext = V(ARGS["extent"], (100, 100, 100))
a.collision_component.set_editor_property("box_extent", ext)
result = {"label": a.get_actor_label(), "extent": [ext.x, ext.y, ext.z]}
""",
            label=label,
            location=location,
            extent=extent,
            _undo="Add trigger volume",
        )

    @mcp.tool(name="unreal_create_input_action")
    async def unreal_create_input_action(
        name: str,
        key: str,
        value_type: str = "bool",
        folder: str = "/Game/Input",
        mapping_context: str = "IMC_Default",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create an Enhanced Input action (``value_type``: bool, axis1d, axis2d,
        axis3d) and map it to ``key`` (e.g. "SpaceBar", "W", "Gamepad_FaceButton_Bottom")
        in a mapping context (created if missing). ``overwrite`` replaces an existing asset at the same path."""
        return await run(
            """
if not has("InputAction"):
    raise RuntimeError("Enhanced Input plugin is not enabled")
types = {"bool": unreal.InputActionValueType.BOOLEAN, "axis1d": unreal.InputActionValueType.AXIS1D,
         "axis2d": unreal.InputActionValueType.AXIS2D, "axis3d": unreal.InputActionValueType.AXIS3D}
ia = new_asset(ARGS["folder"] + "/" + ARGS["name"], unreal.InputAction, unreal.InputAction_Factory())
ia.set_editor_property("value_type", types[ARGS["value_type"].lower()])
ctx_path = ARGS["folder"] + "/" + ARGS["mapping_context"]
imc = unreal.load_asset(ctx_path) if EAL.does_asset_exist(ctx_path) else new_asset(
    ctx_path, unreal.InputMappingContext, unreal.InputMappingContext_Factory())
k = unreal.Key(); k.set_editor_property("key_name", ARGS["key"])
def get_mappings(ctx_asset):
    # UE 5.6+ keeps mappings in default_key_mappings; older versions use mappings.
    try:
        return list(ctx_asset.get_editor_property("default_key_mappings").get_editor_property("mappings"))
    except Exception:
        return list(ctx_asset.get_editor_property("mappings"))
def set_mappings(ctx_asset, maps):
    try:
        dkm = ctx_asset.get_editor_property("default_key_mappings")
        dkm.set_editor_property("mappings", maps)
        ctx_asset.set_editor_property("default_key_mappings", dkm)
    except Exception:
        ctx_asset.set_editor_property("mappings", maps)
def keep(m):
    act = m.get_editor_property("action")
    if act is None:  # left behind by a deleted/overwritten action
        return False
    return not (act.get_name() == ARGS["name"] and
                str(m.get_editor_property("key").get_editor_property("key_name")) == ARGS["key"])
old_maps = get_mappings(imc)
kept = [m for m in old_maps if keep(m)]
if len(kept) != len(old_maps):
    set_mappings(imc, kept)
imc.map_key(ia, k)
def mapping_count(ctx_asset):
    return len(get_mappings(ctx_asset))
EAL.save_loaded_asset(ia); EAL.save_loaded_asset(imc)
result = {"action": ia.get_path_name(), "mapping_context": imc.get_path_name(), "key": ARGS["key"],
          "mappings": mapping_count(imc), "removed_stale": len(old_maps) - len(kept)}
""",
            name=name,
            key=key,
            value_type=value_type,
            folder=folder,
            mapping_context=mapping_context,
            overwrite=overwrite,
            _undo="Create input action",
        )

    @mcp.tool(name="unreal_play_in_editor")
    async def unreal_play_in_editor(simulate: bool = False) -> dict[str, Any]:
        """Start Play-In-Editor (``simulate=true`` for Simulate-In-Editor: physics and
        AI run without a player). Stop with ``unreal_stop_play``."""
        result = await run_python(
            ctx,
            PRELUDE
            + _args(simulate=simulate)
            + """
if LES.is_in_play_in_editor():
    result = {"already_playing": True}
else:
    if ARGS["simulate"]:
        LES.editor_play_simulate()
    else:
        LES.editor_request_begin_play()
    result = {"requested": True, "simulate": ARGS["simulate"]}
""",
        )
        await asyncio.sleep(2)
        return result

    async def _wait_play_ended(timeout: float = 15.0) -> bool:
        """End-play is processed on a later engine tick; wait until it has happened."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            res = await run_python(ctx, PRELUDE + "result = LES.is_in_play_in_editor()")
            if res.get("success") and not res["result"]["result"]:
                return True
            await asyncio.sleep(0.5)
        return False

    @mcp.tool(name="unreal_stop_play")
    async def unreal_stop_play() -> dict[str, Any]:
        """Stop Play/Simulate-In-Editor and wait until the editor is editable again."""
        res = await run_python(
            ctx,
            PRELUDE
            + """
playing = LES.is_in_play_in_editor()
if playing:
    LES.editor_request_end_play()
result = {"was_playing": playing}
""",
        )
        if res.get("success") and res["result"]["result"]["was_playing"]:
            res["result"]["result"]["stopped"] = await _wait_play_ended()
        return res

    # =============================================================================
    # FILM / VIDEO
    # =============================================================================

    @mcp.tool(name="unreal_create_cinematic")
    async def unreal_create_cinematic(
        path: str = "/Game/Cinematics/SEQ_Shot01",
        duration_seconds: float = 5.0,
        fps: int = 24,
        camera_label: str = "ShotCam",
        start: dict[str, Any] | None = None,
        end: dict[str, Any] | None = None,
        focal_length: float = 35.0,
        aperture: float = 2.8,
        look_at: str = "",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create a Level Sequence with a CineCameraActor, a camera cut, and a
        keyframed camera move from ``start`` to ``end`` ({"location": {x,y,z},
        "rotation": {pitch,yaw,roll}}). ``look_at`` aims both keys at an actor and
        focuses on it. Render it with ``unreal_render_sequence_mrq``. ``overwrite`` replaces an existing asset at the same path."""
        return await run(
            """
target = find(ARGS["look_at"]) if ARGS["look_at"] else None
seq = new_asset(ARGS["path"], unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
fps = int(ARGS["fps"]); frames = int(round(ARGS["duration_seconds"] * fps))
seq.set_display_rate(unreal.FrameRate(fps, 1))
seq.set_playback_start(0); seq.set_playback_end(frames)
s = ARGS["start"] or {"location": {"x": -800, "y": 0, "z": 300}, "rotation": {"pitch": -10, "yaw": 0}}
e = ARGS["end"] or {"location": {"x": -400, "y": 400, "z": 250}, "rotation": {"pitch": -10, "yaw": -30}}
def aim(k):
    if not ARGS["look_at"]:
        return R(k.get("rotation"))
    t = target.get_actor_location()
    return unreal.MathLibrary.find_look_at_rotation(V(k.get("location")), t)
cam = spawn(unreal.CineCameraActor, ARGS["camera_label"], s.get("location"), aim(s))
cc = cam.get_cine_camera_component()
cc.set_editor_property("current_focal_length", float(ARGS["focal_length"]))
cc.set_editor_property("current_aperture", float(ARGS["aperture"]))
if ARGS["look_at"]:
    fs = cc.get_editor_property("focus_settings")
    fs.set_editor_property("focus_method", unreal.CameraFocusMethod.TRACKING)
    tfs = fs.get_editor_property("tracking_focus_settings")
    tfs.set_editor_property("actor_to_track", target)
    fs.set_editor_property("tracking_focus_settings", tfs)
    cc.set_editor_property("focus_settings", fs)
binding = seq.add_possessable(cam)
tr = binding.add_track(unreal.MovieScene3DTransformTrack)
sec = tr.add_section(); sec.set_range(0, frames)
ch = sec.get_all_channels()
def key(frame, loc, rot):
    vals = [loc.x, loc.y, loc.z, rot.roll, rot.pitch, rot.yaw]
    for i, v in enumerate(vals):
        ch[i].add_key(unreal.FrameNumber(frame), v)
key(0, V(s.get("location")), aim(s))
key(frames, V(e.get("location")), aim(e))
cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
cs = cut.add_section(); cs.set_range(0, frames)
cs.set_camera_binding_id(seq.get_binding_id(binding))
EAL.save_loaded_asset(seq)
result = {"sequence": seq.get_path_name(), "camera": cam.get_actor_label(), "frames": frames, "fps": fps}
""",
            path=path,
            duration_seconds=duration_seconds,
            fps=fps,
            camera_label=camera_label,
            start=start,
            end=end,
            focal_length=focal_length,
            aperture=aperture,
            look_at=look_at,
            overwrite=overwrite,
            _undo="Create cinematic",
        )

    @mcp.tool(name="unreal_add_transform_keys")
    async def unreal_add_transform_keys(
        sequence: str, actor: str, keys: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Animate an actor in a Level Sequence. ``keys``: [{"time": seconds,
        "location": {x,y,z}, "rotation": {pitch,yaw,roll}, "scale": {x,y,z}}].
        Missing fields keep the actor's current value."""
        return await run(
            """
seq = unreal.load_asset(ARGS["sequence"])
if seq is None:
    raise ValueError("Sequence not found")
a = find(ARGS["actor"])
binding = None
for b in seq.get_bindings():
    if b.get_display_name() == a.get_actor_label():
        binding = b
binding = binding or seq.add_possessable(a)
trs = binding.find_tracks_by_exact_type(unreal.MovieScene3DTransformTrack)
tr = trs[0] if trs else binding.add_track(unreal.MovieScene3DTransformTrack)
secs = tr.get_sections()
sec = secs[0] if secs else tr.add_section()
sec.set_range(seq.get_playback_start(), seq.get_playback_end())
ch = sec.get_all_channels()
rate = seq.get_display_rate().numerator / float(seq.get_display_rate().denominator)
n = 0
for k in ARGS["keys"]:
    f = unreal.FrameNumber(int(round(float(k["time"]) * rate)))
    loc = V(k.get("location"), (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z))
    cur = a.get_actor_rotation()
    rot = R(k.get("rotation"), (cur.pitch, cur.yaw, cur.roll))
    sc = a.get_actor_scale3d()
    scl = V(k.get("scale"), (sc.x, sc.y, sc.z))
    for i, v in enumerate([loc.x, loc.y, loc.z, rot.roll, rot.pitch, rot.yaw, scl.x, scl.y, scl.z]):
        ch[i].add_key(f, v)
    n += 1
EAL.save_loaded_asset(seq)
result = {"sequence": seq.get_path_name(), "actor": a.get_actor_label(), "keys": n}
""",
            sequence=sequence,
            actor=actor,
            keys=keys,
            _undo="Add transform keys",
        )

    @mcp.tool(name="unreal_set_cine_camera")
    async def unreal_set_cine_camera(
        label: str,
        focal_length: float | None = None,
        aperture: float | None = None,
        focus_distance: float | None = None,
        sensor_width: float | None = None,
        sensor_height: float | None = None,
    ) -> dict[str, Any]:
        """Set CineCamera lens settings: focal length (mm), aperture (f-stop),
        manual focus distance (cm) and filmback (mm)."""
        return await run(
            """
cc = find(ARGS["label"]).get_cine_camera_component()
if ARGS["focal_length"] is not None: cc.set_editor_property("current_focal_length", float(ARGS["focal_length"]))
if ARGS["aperture"] is not None: cc.set_editor_property("current_aperture", float(ARGS["aperture"]))
if ARGS["focus_distance"] is not None:
    fs = cc.get_editor_property("focus_settings")
    fs.set_editor_property("focus_method", unreal.CameraFocusMethod.MANUAL)
    fs.set_editor_property("manual_focus_distance", float(ARGS["focus_distance"]))
    cc.set_editor_property("focus_settings", fs)
fb = cc.get_editor_property("filmback")
if ARGS["sensor_width"] is not None: fb.set_editor_property("sensor_width", float(ARGS["sensor_width"]))
if ARGS["sensor_height"] is not None: fb.set_editor_property("sensor_height", float(ARGS["sensor_height"]))
cc.set_editor_property("filmback", fb)
result = {"focal_length": cc.get_editor_property("current_focal_length"),
          "aperture": cc.get_editor_property("current_aperture"),
          "sensor": [fb.get_editor_property("sensor_width"), fb.get_editor_property("sensor_height")]}
""",
            label=label,
            focal_length=focal_length,
            aperture=aperture,
            focus_distance=focus_distance,
            sensor_width=sensor_width,
            sensor_height=sensor_height,
            _undo="Set cine camera",
        )

    @mcp.tool(name="unreal_list_level_sequences")
    async def unreal_list_level_sequences(folder: str = "/Game") -> dict[str, Any]:
        """List Level Sequence assets with frame rate and length."""
        return await run_python(
            ctx,
            PRELUDE
            + _args(folder=folder)
            + """
reg = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
for d in reg.get_assets_by_path(ARGS["folder"], recursive=True):
    if str(d.asset_class_path.asset_name) != "LevelSequence":
        continue
    s = d.get_asset(); r = s.get_display_rate()
    out.append({"path": str(d.package_name), "fps": r.numerator / float(r.denominator),
                "frames": s.get_playback_end() - s.get_playback_start(),
                "bindings": [b.get_display_name() for b in s.get_bindings()]})
result = {"sequences": out}
""",
        )

    @mcp.tool(name="unreal_render_sequence_mrq")
    async def unreal_render_sequence_mrq(
        sequence: str,
        output_directory: str = "",
        file_format: str = "png",
        width: int = 1920,
        height: int = 1080,
        file_name: str = "{sequence_name}.{frame_number}",
    ) -> dict[str, Any]:
        """Render a Level Sequence with Movie Render Queue (needs the Movie Render
        Queue plugin). ``file_format``: png, jpg, exr, bmp. Rendering runs
        asynchronously in a PIE session; poll ``unreal_get_render_status``. The
        current level must be saved (MRQ renders the saved map)."""
        return await run_python(
            ctx,
            PRELUDE
            + _args(
                sequence=sequence,
                out=output_directory,
                fmt=file_format.lower(),
                w=width,
                h=height,
                fn=file_name,
            )
            + """
if not has("MoviePipelineQueueSubsystem"):
    raise RuntimeError("Movie Render Queue plugin (MovieRenderPipeline) is not enabled")
subsys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
if subsys.is_rendering():
    raise RuntimeError("A render is already in progress")
w = world()
pkg = w.get_outermost().get_name()
if pkg.startswith("/Temp/"):
    raise RuntimeError("Save the level first (unreal_save_level); MRQ renders the saved map")
queue = subsys.get_queue()
queue.delete_all_jobs()
job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
job.sequence = unreal.SoftObjectPath(ARGS["sequence"])
job.map = unreal.SoftObjectPath(pkg)
job.job_name = ARGS["sequence"].rsplit("/", 1)[-1]
cfg = job.get_configuration()
out = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
outdir = ARGS["out"] or (unreal.Paths.project_saved_dir() + "MovieRenders")
out.output_directory = unreal.DirectoryPath(outdir)
out.output_resolution = unreal.IntPoint(int(ARGS["w"]), int(ARGS["h"]))
# {sequence_name} can resolve empty for queue jobs (frames named ".0001.png"),
# so substitute the real name up front.
seq_name = ARGS["sequence"].rsplit("/", 1)[-1].split(".")[0]
out.file_name_format = ARGS["fn"].replace("{sequence_name}", seq_name)
fmts = {"png": unreal.MoviePipelineImageSequenceOutput_PNG, "jpg": unreal.MoviePipelineImageSequenceOutput_JPG,
        "exr": unreal.MoviePipelineImageSequenceOutput_EXR, "bmp": unreal.MoviePipelineImageSequenceOutput_BMP}
if ARGS["fmt"] not in fmts:
    raise ValueError("file_format must be one of " + ", ".join(fmts))
cfg.find_or_add_setting_by_class(fmts[ARGS["fmt"]])
cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
subsys.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
result = {"started": True, "output_directory": outdir, "format": ARGS["fmt"]}
""",
        )

    @mcp.tool(name="unreal_get_render_status")
    async def unreal_get_render_status(output_directory: str = "") -> dict[str, Any]:
        """Is a Movie Render Queue render running? Also counts frames written to
        ``output_directory`` (default Saved/MovieRenders)."""
        status = await run_python(
            ctx,
            """
s = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem) if hasattr(unreal, "MoviePipelineQueueSubsystem") else None
result = {"rendering": bool(s and s.is_rendering()),
          "default_output": unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir() + "MovieRenders")}
""",
        )
        if status.get("success"):
            info = status["result"]["result"]
            folder = Path(output_directory or info["default_output"])
            frames = (
                sorted(p.name for p in folder.glob("*") if p.is_file()) if folder.is_dir() else []
            )
            info["files_written"] = len(frames)
            info["last_files"] = frames[-3:]
        return status

    # =============================================================================
    # LIVE EVENTS / VIRTUAL PRODUCTION
    # =============================================================================

    @mcp.tool(name="unreal_get_virtual_production_status")
    async def unreal_get_virtual_production_status() -> dict[str, Any]:
        """Which virtual-production / live-event features are available (nDisplay,
        Live Link, DMX, OpenColorIO, Remote Control, Media Framework) and which nDisplay
        configs exist in the project."""
        return await run_python(
            ctx,
            PRELUDE
            + """
feats = {"ndisplay": "DisplayClusterRootActor", "live_link": "LiveLinkBlueprintLibrary",
         "dmx": "DMXLibrary", "opencolorio": "OpenColorIOConfiguration",
         "remote_control": "RemoteControlPreset", "media_framework": "MediaPlayer",
         "virtual_camera": "VCamComponent", "movie_render_queue": "MoviePipelineQueueSubsystem",
         "variant_manager": "LevelVariantSets", "datasmith": "DatasmithSceneElement"}
avail = {k: has(v) for k, v in feats.items()}
configs = []
if avail["ndisplay"]:
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for d in reg.get_assets_by_path("/Game", recursive=True):
        if "DisplayCluster" in str(d.asset_class_path.asset_name):
            configs.append(str(d.package_name))
result = {"features": avail, "ndisplay_configs": configs}
""",
        )

    @mcp.tool(name="unreal_list_livelink_subjects")
    async def unreal_list_livelink_subjects() -> dict[str, Any]:
        """List Live Link subjects (mocap, camera tracking, face capture sources)."""
        return await run_python(
            ctx,
            """
if not hasattr(unreal, "LiveLinkBlueprintLibrary"):
    raise RuntimeError("Live Link plugin is not enabled")
subs = unreal.LiveLinkBlueprintLibrary.get_live_link_subjects(True, True)
result = {"subjects": [{"name": str(s.subject_name.name), "source": str(s.source)} for s in subs]}
""",
        )

    @mcp.tool(name="unreal_create_led_stage")
    async def unreal_create_led_stage(
        radius: float = 800.0,
        arc_degrees: float = 180.0,
        height: float = 500.0,
        segments: int = 16,
        ceiling: bool = True,
        center: dict[str, float] | None = None,
        label: str = "LEDStage",
    ) -> dict[str, Any]:
        """Block out an ICVFX LED volume: a curved wall of panels, a floor, an optional
        ceiling and a tracked CineCamera at the centre, all grouped under one root.
        Use for stage planning / previs; pair with nDisplay configs for real output."""
        return await run(
            """
c = V(ARGS["center"])
root = spawn(unreal.Actor, ARGS["label"], c)
root.set_root_component(unreal.SceneComponent()) if root.root_component is None else None
n = max(3, int(ARGS["segments"])); arc = math.radians(ARGS["arc_degrees"])
r = float(ARGS["radius"]); h = float(ARGS["height"])
seg_w = 2 * r * math.sin(arc / n / 2)
panels = []
for i in range(n):
    t = -arc / 2 + arc * (i + 0.5) / n
    x, y = c.x + r * math.cos(t), c.y + r * math.sin(t)
    p = spawn_mesh("%s_Panel_%02d" % (ARGS["label"], i), "cube", (x, y, c.z + h / 2),
                   (0, math.degrees(t), 0), (0.1, seg_w / 100.0, h / 100.0))
    p.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                      unreal.AttachmentRule.KEEP_WORLD, False)
    panels.append(p.get_actor_label())
fl = spawn_mesh(ARGS["label"] + "_Floor", "cylinder", (c.x, c.y, c.z - 5), None, (r / 50.0, r / 50.0, 0.1))
fl.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
if ARGS["ceiling"]:
    ce = spawn_mesh(ARGS["label"] + "_Ceiling", "cylinder", (c.x, c.y, c.z + h + 20), None, (r / 50.0, r / 50.0, 0.1))
    ce.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
cam = spawn(unreal.CineCameraActor, ARGS["label"] + "_TrackedCamera", (c.x - r * 0.4, c.y, c.z + 170), (0, 0, 0))
for _x in SPAWNED:
    _x.set_folder_path(ARGS["label"])
result ={"root": root.get_actor_label(), "panels": len(panels), "panel_width_cm": round(seg_w, 1),
          "camera": cam.get_actor_label()}
""",
            radius=radius,
            arc_degrees=arc_degrees,
            height=height,
            segments=segments,
            ceiling=ceiling,
            center=center,
            label=label,
            _undo="Create LED stage",
        )

    @mcp.tool(name="unreal_create_lighting_cue")
    async def unreal_create_lighting_cue(
        path: str,
        cues: list[dict[str, Any]],
        fps: int = 30,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create a show-control Level Sequence that animates lights. ``cues``:
        [{"light": "Label", "time": seconds, "intensity": 5000, "color": {r,g,b}}].
        Play it in the editor, in PIE, or trigger it from Blueprints at runtime. ``overwrite`` replaces an existing asset at the same path."""
        return await run(
            """
for c in ARGS["cues"]:
    if find(c["light"]).get_component_by_class(unreal.LightComponent) is None:
        raise ValueError("%s has no light component" % c["light"])
seq = new_asset(ARGS["path"], unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
fps = int(ARGS["fps"]); seq.set_display_rate(unreal.FrameRate(fps, 1))
end = max(float(c["time"]) for c in ARGS["cues"]) if ARGS["cues"] else 1.0
seq.set_playback_start(0); seq.set_playback_end(int(round(end * fps)) + 1)
tracks = {}
for c in sorted(ARGS["cues"], key=lambda c: float(c["time"])):
    a = find(c["light"])
    comp = a.get_component_by_class(unreal.LightComponent)
    if comp is None:
        raise ValueError("%s has no light component" % c["light"])
    if c["light"] not in tracks:
        actor_b = seq.add_possessable(a)
        comp_b = seq.add_possessable(comp)
        comp_b.set_parent(actor_b)
        it = comp_b.add_track(unreal.MovieSceneFloatTrack); it.set_property_name_and_path("Intensity", "Intensity")
        isec = it.add_section(); isec.set_range(0, seq.get_playback_end())
        ct = comp_b.add_track(unreal.MovieSceneColorTrack); ct.set_property_name_and_path("Light Color", "LightColor")
        csec = ct.add_section(); csec.set_range(0, seq.get_playback_end())
        tracks[c["light"]] = (isec.get_all_channels(), csec.get_all_channels())
    ich, cch = tracks[c["light"]]
    f = unreal.FrameNumber(int(round(float(c["time"]) * fps)))
    if "intensity" in c:
        ich[0].add_key(f, float(c["intensity"]))
    if "color" in c:
        col = c["color"]
        for i, k in enumerate(("r", "g", "b")):
            cch[i].add_key(f, float(col[k]))
        cch[3].add_key(f, float(col.get("a", 1.0)))
EAL.save_loaded_asset(seq)
result = {"sequence": seq.get_path_name(), "lights": list(tracks), "cues": len(ARGS["cues"]),
          "seconds": end}
""",
            path=path,
            cues=cues,
            fps=fps,
            overwrite=overwrite,
            _undo="Create lighting cue",
        )

    @mcp.tool(name="unreal_create_display_wall")
    async def unreal_create_display_wall(
        label: str = "DisplayWall",
        location: dict[str, float] | None = None,
        yaw: float = 0.0,
        rows: int = 2,
        columns: int = 4,
        panel_width: float = 200.0,
        panel_height: float = 112.5,
        gap: float = 5.0,
        emissive_material: str = "",
    ) -> dict[str, Any]:
        """Build a broadcast/event display wall: a grid of screen panels (16:9 by
        default) on a frame. ``emissive_material`` (e.g. a media texture material) is
        applied to every screen."""
        return await run(
            """
o = V(ARGS["location"]); yaw = math.radians(ARGS["yaw"])
rows, cols = int(ARGS["rows"]), int(ARGS["columns"])
pw, ph, g = float(ARGS["panel_width"]), float(ARGS["panel_height"]), float(ARGS["gap"])
tw, th = cols * pw + (cols - 1) * g, rows * ph + (rows - 1) * g
names = []
for rr in range(rows):
    for cc in range(cols):
        u = -tw / 2 + pw / 2 + cc * (pw + g); z = o.z + ph / 2 + rr * (ph + g)
        x, y = o.x - u * math.sin(yaw), o.y + u * math.cos(yaw)
        p = spawn_mesh("%s_Screen_%d_%d" % (ARGS["label"], rr, cc), "cube", (x, y, z), (0, ARGS["yaw"], 0),
                       (0.05, pw / 100.0, ph / 100.0), ARGS["emissive_material"] or None)
        names.append(p.get_actor_label())
frame = spawn_mesh(ARGS["label"] + "_Frame", "cube", (o.x - 10 * math.cos(yaw), o.y - 10 * math.sin(yaw), o.z + th / 2),
                   (0, ARGS["yaw"], 0), (0.1, (tw + 40) / 100.0, (th + 40) / 100.0))
for _x in SPAWNED:
    _x.set_folder_path(ARGS["label"])
result ={"screens": len(names), "size_cm": [round(tw, 1), round(th, 1)], "frame": frame.get_actor_label()}
""",
            label=label,
            location=location,
            yaw=yaw,
            rows=rows,
            columns=columns,
            panel_width=panel_width,
            panel_height=panel_height,
            gap=gap,
            emissive_material=emissive_material,
            _undo="Create display wall",
        )

    # =============================================================================
    # AUTOMOTIVE / PRODUCT DESIGN / MANUFACTURING VISUALISATION
    # =============================================================================

    @mcp.tool(name="unreal_import_cad")
    async def unreal_import_cad(
        file_path: str,
        destination: str = "/Game/Imported",
        place_in_level: bool = True,
        location: dict[str, float] | None = None,
        timeout: float = 600.0,
    ) -> dict[str, Any]:
        """Import CAD / DCC geometry. FBX, OBJ, glTF/GLB and USD go through the
        standard importer; STEP, IGES, JT, CATIA, SolidWorks, Rhino (3dm) and
        .udatasmith go through Datasmith (needs the Datasmith importer plugins).
        Imported meshes are placed in the level unless ``place_in_level=false``."""
        p = Path(file_path)
        if not p.is_file():
            return fail(f"File not found: {file_path}", code="invalid_params")
        return await run(
            """
ext = ARGS["file"].rsplit(".", 1)[-1].lower()
cad = {"step", "stp", "iges", "igs", "jt", "catpart", "catproduct", "sldprt", "sldasm",
       "3dm", "prt", "x_t", "sat", "udatasmith", "ifc", "wire"}
placed = []
ensure_dir(ARGS["dest"])
if ext in cad:
    if not has("DatasmithSceneElement"):
        raise RuntimeError("Datasmith importer plugin is not enabled (needed for .%s)" % ext)
    scene = unreal.DatasmithSceneElement.construct_datasmith_scene_from_file(ARGS["file"])
    if scene is None:
        raise RuntimeError("Datasmith could not read %s" % ARGS["file"])
    res = scene.import_scene(ARGS["dest"])
    meshes = [m.get_path_name() for m in (res.imported_meshes or [])]
    placed = [a.get_actor_label() for a in (res.imported_actors or [])]
    scene.destroy_scene()
    via = "datasmith"
else:
    task = unreal.AssetImportTask()
    task.filename = ARGS["file"]; task.destination_path = ARGS["dest"]
    task.automated = True; task.replace_existing = True; task.save = True
    AT.import_asset_tasks([task])
    paths = list(task.imported_object_paths or [])
    meshes = [p for p in paths if isinstance(unreal.load_asset(p), unreal.StaticMesh)]
    via = "asset_import"
    if ARGS["place"]:
        o = V(ARGS["location"])
        for p in meshes:
            a = EAS.spawn_actor_from_object(unreal.load_asset(p), o)
            placed.append(a.get_actor_label())
if not meshes and not placed:
    raise RuntimeError("Nothing was imported from %s" % ARGS["file"])
result = {"via": via, "meshes": meshes[:50], "mesh_count": len(meshes), "placed": placed[:50]}
""",
            timeout=timeout,
            file=str(p.resolve()),
            dest=destination,
            place=place_in_level,
            location=location,
            _undo="Import CAD",
        )

    @mcp.tool(name="unreal_create_product_studio")
    async def unreal_create_product_studio(
        center: dict[str, float] | None = None,
        size: float = 2000.0,
        backdrop_color: dict[str, float] | None = None,
        label: str = "Studio",
    ) -> dict[str, Any]:
        """Product / automotive photo studio: seamless cyclorama (floor + curved back),
        key/fill/rim rect lights, a sky light and a reflective-friendly backdrop
        colour. Put the product at ``center``."""
        return await run(
            """
c = V(ARGS["center"]); s = float(ARGS["size"])
col = ARGS["backdrop_color"] or {"r": 0.8, "g": 0.8, "b": 0.82}
mat_path = "/Game/Studio/MI_Cyclorama"
if EAL.does_asset_exist(mat_path):
    mi = unreal.load_asset(mat_path)
else:
    mi = new_asset(mat_path, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(
        mi, unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    mi, "Color", unreal.LinearColor(col["r"], col["g"], col["b"], 1.0))
unreal.MaterialEditingLibrary.update_material_instance(mi)
parts = []
floor = spawn_mesh(ARGS["label"] + "_Floor", "cube", (c.x, c.y, c.z - 5), None, (s / 100.0, s / 100.0, 0.1), mat_path)
parts.append(floor)
# Curved cove: quarter circle of thin slats joining the floor to the back wall.
r = s * 0.25; n = 8
for i in range(n):
    t = (i + 0.5) / n * (math.pi / 2)
    x = c.x + s / 2 - r + r * math.sin(t); z = c.z + r - r * math.cos(t)
    seg = 2 * r * math.sin(math.pi / 4 / n)
    p = spawn_mesh("%s_Cove_%d" % (ARGS["label"], i), "cube", (x, c.y, z), (math.degrees(t), 0, 0),
                   (seg / 100.0 + 0.02, s / 100.0, 0.1), mat_path)
    parts.append(p)
back = spawn_mesh(ARGS["label"] + "_Back", "cube", (c.x + s / 2, c.y, c.z + r + s * 0.3), None,
                  (0.1, s / 100.0, s * 0.6 / 100.0), mat_path)
parts.append(back)
def rect(name, loc, intensity, w, h):
    l = spawn(unreal.RectLight, ARGS["label"] + "_" + name, loc)
    l.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(loc), c), False)
    rc = l.get_component_by_class(unreal.RectLightComponent)
    rc.set_editor_property("intensity", intensity)
    rc.set_editor_property("source_width", w); rc.set_editor_property("source_height", h)
    rc.set_editor_property("attenuation_radius", s * 2)
    return l
key = rect("Key", (c.x - s * 0.3, c.y - s * 0.35, c.z + s * 0.3), 60.0, 300, 300)
fill = rect("Fill", (c.x - s * 0.3, c.y + s * 0.4, c.z + s * 0.15), 20.0, 400, 300)
rim = rect("Rim", (c.x + s * 0.3, c.y, c.z + s * 0.35), 40.0, 200, 400)
sky = spawn(unreal.SkyLight, ARGS["label"] + "_SkyLight", (c.x, c.y, c.z + s * 0.5))
sky.light_component.set_editor_property("intensity", 0.5)
for p in parts + [key, fill, rim, sky]:
    p.set_folder_path(ARGS["label"])
result = {"parts": len(parts), "lights": ["Key", "Fill", "Rim", "SkyLight"], "material": mat_path}
""",
            center=center,
            size=size,
            backdrop_color=backdrop_color,
            label=label,
            _undo="Create product studio",
        )

    @mcp.tool(name="unreal_create_turntable")
    async def unreal_create_turntable(
        target: str,
        seconds: float = 8.0,
        fps: int = 30,
        sequence_path: str = "/Game/Cinematics/SEQ_Turntable",
        platform: bool = True,
        camera_distance: float = 0.0,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Product turntable: put ``target`` on a rotating platform, animate one full
        rotation over ``seconds`` in a Level Sequence, and frame it with a CineCamera
        (distance auto-fits the product's bounds when 0). Render with
        ``unreal_render_sequence_mrq``. ``overwrite`` replaces an existing asset at the same path."""
        return await run(
            """
t = find(ARGS["target"])
o, e = t.get_actor_bounds(False)
radius = max(e.x, e.y, 50.0)
pivot = spawn(unreal.Actor, ARGS["target"] + "_Turntable", (o.x, o.y, o.z - e.z))
if pivot.root_component is None:
    sc = pivot.add_component_by_class(unreal.SceneComponent, False, unreal.Transform(), False) if hasattr(pivot, "add_component_by_class") else None
if ARGS["platform"]:
    plat = spawn_mesh(ARGS["target"] + "_Platform", "cylinder", (o.x, o.y, o.z - e.z - 5), None,
                      (radius * 2.4 / 100.0, radius * 2.4 / 100.0, 0.1))
    plat.attach_to_actor(pivot, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
t.attach_to_actor(pivot, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
seq = new_asset(ARGS["seq"], unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
fps = int(ARGS["fps"]); frames = int(round(float(ARGS["seconds"]) * fps))
seq.set_display_rate(unreal.FrameRate(fps, 1)); seq.set_playback_start(0); seq.set_playback_end(frames)
b = seq.add_possessable(pivot)
tr = b.add_track(unreal.MovieScene3DTransformTrack); sec = tr.add_section(); sec.set_range(0, frames)
ch = sec.get_all_channels()
pl = pivot.get_actor_location()
for f, yaw in ((0, 0.0), (frames, 360.0)):
    for i, v in enumerate([pl.x, pl.y, pl.z, 0.0, 0.0, yaw]):
        ch[i].add_key(unreal.FrameNumber(f), v)
for k in ch[5].get_keys():
    k.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)
dist = float(ARGS["camera_distance"]) or max(e.x, e.y, e.z) * 3.2
cam_loc = unreal.Vector(o.x - dist, o.y, o.z + e.z * 0.6)
cam = spawn(unreal.CineCameraActor, ARGS["target"] + "_TurntableCam", cam_loc,
            unreal.MathLibrary.find_look_at_rotation(cam_loc, o))
cb = seq.add_possessable(cam)
cut = seq.add_track(unreal.MovieSceneCameraCutTrack); cs = cut.add_section(); cs.set_range(0, frames)
cs.set_camera_binding_id(seq.get_binding_id(cb))
EAL.save_loaded_asset(seq)
result = {"sequence": seq.get_path_name(), "pivot": pivot.get_actor_label(), "camera": cam.get_actor_label(),
          "frames": frames}
""",
            target=target,
            seconds=seconds,
            fps=fps,
            seq=sequence_path,
            platform=platform,
            camera_distance=camera_distance,
            overwrite=overwrite,
            _undo="Create turntable",
        )

    @mcp.tool(name="unreal_create_variant_set")
    async def unreal_create_variant_set(
        asset_path: str,
        set_name: str,
        actor: str,
        variants: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Configurator (Variant Manager): create/extend a Level Variant Sets asset with
        a variant set for ``actor``. ``variants``: [{"name": "Red", "material":
        "/Game/Paint/MI_Red"}] (material slot 0) or [{"name": "Hidden", "visible":
        false}]. Adds a LevelVariantSetsActor to the level so variants can be switched
        at runtime and with ``unreal_activate_variant``."""
        return await run(
            """
if not has("LevelVariantSets"):
    raise RuntimeError("Variant Manager plugin is not enabled")
folder, name = split(ARGS["asset"])
ensure_dir(folder)
lvs = unreal.load_asset(folder + "/" + name) if EAL.does_asset_exist(folder + "/" + name) else \\
    unreal.VariantManagerLibrary.create_level_variant_sets_asset(name, folder)
a = find(ARGS["actor"])
replaced = lvs.get_variant_set_by_name(ARGS["set_name"]) is not None
if replaced:  # re-running replaces the set instead of adding "Paint0", "Paint1", ...
    unreal.VariantManagerLibrary.remove_variant_set_by_name(lvs, ARGS["set_name"])
vs = unreal.VariantSet(); vs.set_display_text(ARGS["set_name"])
unreal.VariantManagerLibrary.add_variant_set(lvs, vs)
made = []
for spec in ARGS["variants"]:
    var = unreal.Variant(); var.set_display_text(spec["name"])
    unreal.VariantManagerLibrary.add_variant(vs, var)
    unreal.VariantManagerLibrary.add_actor_binding(var, a)
    if "material" in spec:
        mat = unreal.load_asset(spec["material"])
        if mat is None:
            raise ValueError("Material not found: " + spec["material"])
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        old = comp.get_material(0)
        comp.set_material(0, mat)
        caps = unreal.VariantManagerLibrary.get_capturable_properties(a)
        path = next((p for p in caps if "Material[0]" in p), None)
        if path is None:
            raise RuntimeError("No capturable material slot on %s" % ARGS["actor"])
        prop = unreal.VariantManagerLibrary.capture_property(var, a, path)
        unreal.VariantManagerLibrary.record(prop)
        comp.set_material(0, old)
    if "visible" in spec:
        was = not a.is_hidden_ed()
        a.set_is_temporarily_hidden_in_editor(not spec["visible"])
        a.root_component.set_editor_property("visible", bool(spec["visible"]))
        prop = unreal.VariantManagerLibrary.capture_property(var, a, "Root Component / Visible")
        unreal.VariantManagerLibrary.record(prop)
        a.root_component.set_editor_property("visible", was)
        a.set_is_temporarily_hidden_in_editor(not was)
    made.append(spec["name"])
lva = None
for x in EAS.get_all_level_actors():
    if isinstance(x, unreal.LevelVariantSetsActor) and x.get_level_variant_sets(False) == lvs:
        lva = x
if lva is None:
    lva = unreal.VariantManagerLibrary.create_level_variant_sets_actor(lvs)
EAL.save_loaded_asset(lvs)
result = {"asset": lvs.get_path_name(), "set": ARGS["set_name"], "replaced": replaced, "variants": made,
          "actor": lva.get_actor_label() if lva else None}
""",
            asset=asset_path,
            set_name=set_name,
            actor=actor,
            variants=variants,
            _undo="Create variant set",
        )

    @mcp.tool(name="unreal_activate_variant")
    async def unreal_activate_variant(
        asset_path: str, set_name: str, variant: str
    ) -> dict[str, Any]:
        """Switch a Variant Manager configurator to ``variant`` in ``set_name``
        (e.g. paint colour, trim, wheel option)."""
        return await run(
            """
lvs = unreal.load_asset(ARGS["asset"])
if lvs is None:
    raise ValueError("Level Variant Sets asset not found")
for x in EAS.get_all_level_actors():
    if isinstance(x, unreal.LevelVariantSetsActor) and x.get_level_variant_sets(False) == lvs:
        ok = x.switch_on_variant_by_name(ARGS["set_name"], ARGS["variant"])
        result = {"switched": bool(ok), "set": ARGS["set_name"], "variant": ARGS["variant"]}
        break
else:
    raise RuntimeError("No LevelVariantSetsActor for this asset in the level")
""",
            asset=asset_path,
            set_name=set_name,
            variant=variant,
            _undo="Activate variant",
        )

    @mcp.tool(name="unreal_measure")
    async def unreal_measure(actors: list[str], unit: str = "cm") -> dict[str, Any]:
        """Measure actors: bounding-box size of each (``unit``: cm, mm, m, in) and the
        centre-to-centre and closest-surface distance between the first two."""
        return await run_python(
            ctx,
            PRELUDE
            + _args(actors=actors, unit=unit)
            + """
f = {"cm": 1.0, "mm": 10.0, "m": 0.01, "in": 1 / 2.54}[ARGS["unit"]]
out = []; boxes = []
for n in ARGS["actors"]:
    a = find(n); o, e = a.get_actor_bounds(False)
    boxes.append((o, e))
    out.append({"actor": n, "size": [round(2 * e.x * f, 2), round(2 * e.y * f, 2), round(2 * e.z * f, 2)],
                "center": [round(o.x * f, 2), round(o.y * f, 2), round(o.z * f, 2)]})
res = {"unit": ARGS["unit"], "actors": out}
if len(boxes) >= 2:
    (o1, e1), (o2, e2) = boxes[:2]
    res["center_distance"] = round((o2 - o1).length() * f, 2)
    gap = [max(0.0, abs(a - b) - (c + d)) for a, b, c, d in ((o1.x, o2.x, e1.x, e2.x), (o1.y, o2.y, e1.y, e2.y), (o1.z, o2.z, e1.z, e2.z))]
    res["surface_gap"] = round(math.sqrt(sum(g * g for g in gap)) * f, 2)
result = res
""",
        )

    # =============================================================================
    # SIMULATION / DIGITAL TWIN / TRAINING
    # =============================================================================

    @mcp.tool(name="unreal_spawn_from_data")
    async def unreal_spawn_from_data(
        records: list[dict[str, Any]], folder: str = ""
    ) -> dict[str, Any]:
        """Digital twin / data-driven layout: spawn or update actors from records.
        Each record: {"label", "mesh" (cube/sphere/cylinder/cone/plane or asset path),
        "location", "rotation", "scale", "material", "physics": bool, "mass": kg}.
        Existing labels are moved/updated instead of duplicated."""
        return await run(
            """
created, updated = [], []
for r in ARGS["records"]:
    try:
        a = find(r["label"]); updated.append(r["label"])
        a.set_actor_location(V(r.get("location"), (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)), False, False)
        if r.get("rotation") is not None: a.set_actor_rotation(R(r["rotation"]), False)
        if r.get("scale") is not None: a.set_actor_scale3d(V(r["scale"]))
    except ValueError:
        a = spawn_mesh(r["label"], r.get("mesh", "cube"), r.get("location"), r.get("rotation"), r.get("scale"))
        created.append(r["label"])
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if r.get("material") and smc:
        smc.set_material(0, unreal.load_asset(r["material"]))
    if smc and r.get("physics") is not None:
        a.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        smc.set_simulate_physics(bool(r["physics"]))
    if smc and r.get("mass") is not None:
        smc.set_mass_override_in_kg("", float(r["mass"]), True)
    if ARGS["folder"]:
        a.set_folder_path(ARGS["folder"])
result = {"created": len(created), "updated": len(updated), "labels": (created + updated)[:100]}
""",
            records=records,
            folder=folder,
            _undo="Spawn from data",
        )

    @mcp.tool(name="unreal_create_conveyor")
    async def unreal_create_conveyor(
        label: str = "Conveyor",
        start: dict[str, float] | None = None,
        length: float = 1200.0,
        width: float = 120.0,
        yaw: float = 0.0,
        parts: int = 6,
        part_size: float = 40.0,
        part_mass: float = 5.0,
        slope_degrees: float = 0.0,
        friction: float = 0.1,
    ) -> dict[str, Any]:
        """Manufacturing line block-out: a conveyor bed with side rails and legs, plus
        ``parts`` physics-enabled boxes spaced along it. ``length`` is measured along the
        belt. Tilt with ``slope_degrees`` so parts slide under gravity in
        ``unreal_run_simulation``; they slide when tan(slope) exceeds ``friction``
        (bed surface friction, applied through a physical material)."""
        return await run(
            """
s = V(ARGS["start"], (0, 0, 80)); L = float(ARGS["length"]); W = float(ARGS["width"])
yaw = float(ARGS["yaw"]); sl = float(ARGS["slope_degrees"])
if not 0 <= sl < 80:
    raise ValueError("slope_degrees must be between 0 and 80")
# ``length`` is measured along the belt; (dx, dy, dz) is the unit belt direction.
ch = math.cos(math.radians(sl))
dx, dy = math.cos(math.radians(yaw)) * ch, math.sin(math.radians(yaw)) * ch
dz = -math.sin(math.radians(sl))
if s.z + dz * L < 1:
    raise ValueError("Low end would be at z=%.0f (below ground). Raise start.z to at least %.0f, "
                     "shorten length or reduce slope_degrees" % (s.z + dz * L, 1 - dz * L))
mid = unreal.Vector(s.x + dx * L / 2, s.y + dy * L / 2, s.z + dz * L / 2)
bed = spawn_mesh(ARGS["label"] + "_Bed", "cube", mid, (-sl, yaw, 0), (L / 100.0, W / 100.0, 0.1))
fr = max(0.0, float(ARGS["friction"]))
pm_path = "/Game/MCP/Physics/PM_Conveyor_%03d" % int(round(fr * 100))
if EAL.does_asset_exist(pm_path):
    pm = unreal.load_asset(pm_path)
else:
    ensure_dir("/Game/MCP/Physics")
    pm = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        pm_path.rsplit("/", 1)[1], "/Game/MCP/Physics", unreal.PhysicalMaterial, unreal.PhysicalMaterialFactoryNew())
    pm.set_editor_property("friction", fr)
    pm.set_editor_property("static_friction", fr)
    pm.set_editor_property("friction_combine_mode", unreal.FrictionCombineMode.MIN)
    pm.set_editor_property("override_friction_combine_mode", True)
    EAL.save_loaded_asset(pm)
bed.static_mesh_component.set_phys_material_override(pm)
names = [bed.get_actor_label()]
for side in (-1, 1):
    ox, oy = -dy / ch * side * (W / 2 + 5), dx / ch * side * (W / 2 + 5)
    rail = spawn_mesh("%s_Rail_%s" % (ARGS["label"], "L" if side < 0 else "R"), "cube",
                      (mid.x + ox, mid.y + oy, mid.z + 15), (-sl, yaw, 0), (L / 100.0, 0.1, 0.3))
    names.append(rail.get_actor_label())
nl = max(2, int(L // 300) + 1)
for i in range(nl):
    t = i / (nl - 1) * L
    leg_top = s.z + dz * t
    leg = spawn_mesh("%s_Leg_%d" % (ARGS["label"], i), "cube", (s.x + dx * t, s.y + dy * t, leg_top / 2), (0, yaw, 0),
                     (0.1, W / 100.0, max(leg_top, 1) / 100.0))
    names.append(leg.get_actor_label())
ps = float(ARGS["part_size"]); n = int(ARGS["parts"])
lift = 5 + ps / 2 + 1  # bed half-thickness + half part + clearance, along the bed normal
nx, ny, nz = -dz * dx / ch if ch else 0, -dz * dy / ch if ch else 0, ch
items = []
for i in range(n):
    t = (i + 0.5) / n * L * 0.9
    p = spawn_mesh("%s_Part_%02d" % (ARGS["label"], i), "cube",
                   (s.x + dx * t + nx * lift, s.y + dy * t + ny * lift, s.z + dz * t + nz * lift),
                   (-sl, yaw, 0), ps / 100.0)
    p.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    p.static_mesh_component.set_simulate_physics(True)
    p.static_mesh_component.set_mass_override_in_kg("", float(ARGS["part_mass"]), True)
    items.append(p.get_actor_label())
for x in names + items:
    find(x).set_folder_path(ARGS["label"])
result = {"structure": names, "parts": items, "high_end_z": round(s.z, 1),
          "low_end_z": round(s.z + dz * L, 1), "horizontal_run": round(L * ch, 1),
          "friction": fr, "parts_slide": math.tan(math.radians(sl)) > fr}
""",
            label=label,
            start=start,
            length=length,
            width=width,
            yaw=yaw,
            parts=parts,
            part_size=part_size,
            part_mass=part_mass,
            slope_degrees=slope_degrees,
            friction=friction,
            _undo="Create conveyor",
        )

    @mcp.tool(name="unreal_create_physics_stack")
    async def unreal_create_physics_stack(
        label: str = "Stack",
        base: dict[str, float] | None = None,
        rows: int = 4,
        size: float = 50.0,
        mass: float = 10.0,
        shape: str = "cube",
    ) -> dict[str, Any]:
        """Build a pyramid of physics bodies (crates, barrels, spheres) for
        destruction, stability or training scenarios."""
        return await run(
            """
b = V(ARGS["base"]); s = float(ARGS["size"]); names = []
for r in range(int(ARGS["rows"])):
    count = int(ARGS["rows"]) - r
    for c in range(count):
        y = b.y + (c - (count - 1) / 2.0) * s * 1.02
        z = b.z + s / 2 + r * s * 1.01
        p = spawn_mesh("%s_%d_%d" % (ARGS["label"], r, c), ARGS["shape"], (b.x, y, z), None, s / 100.0)
        p.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        p.static_mesh_component.set_simulate_physics(True)
        p.static_mesh_component.set_mass_override_in_kg("", float(ARGS["mass"]), True)
        p.set_folder_path(ARGS["label"])
        names.append(p.get_actor_label())
result = {"bodies": len(names), "labels": names}
""",
            label=label,
            base=base,
            rows=rows,
            size=size,
            mass=mass,
            shape=shape,
            _undo="Create physics stack",
        )

    @mcp.tool(name="unreal_run_simulation")
    async def unreal_run_simulation(
        seconds: float = 3.0,
        track: list[str] | None = None,
        stop_after: bool = True,
    ) -> dict[str, Any]:
        """Run Simulate-In-Editor for ``seconds`` (physics, AI, Niagara) and report
        where the ``track``ed actors ended up versus where they started (all physics
        bodies when ``track`` is empty). The editor level itself is not changed."""
        seconds = max(0.5, min(float(seconds), 120.0))
        throttle_off = await _set_play_throttle_override(True)
        try:
            return await _simulate(seconds, track, stop_after, throttle_off)
        finally:
            if throttle_off:
                await _set_play_throttle_override(False)

    async def _set_play_throttle_override(disabled: bool) -> bool:
        """Ask the plugin to stop background CPU throttling during play (older plugin
        builds lack the command; the simulation then runs slower than real time)."""
        try:
            resp = await ctx.dispatcher.client.request(
                "unreal_set_play_throttle_override", {"disabled": disabled}, retry=False
            )
        except (UnrealEngineMCPError, OSError):
            return False
        return bool(getattr(resp, "ok", False))

    async def _simulate(
        seconds: float, track: list[str] | None, stop_after: bool, throttle_off: bool
    ) -> dict[str, Any]:
        before = await run_python(
            ctx,
            PRELUDE
            + _args(track=track or [])
            + """
if LES.is_in_play_in_editor():
    raise RuntimeError("Already playing; call unreal_stop_play first")
names = ARGS["track"] or [a.get_actor_label() for a in EAS.get_all_level_actors()
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.is_simulating_physics()]
start = {n: loc_list(find(n)) for n in names[:200]}
LES.editor_play_simulate()
result = {"tracked": names[:200], "start": start}
""",
        )
        if not before.get("success"):
            return before
        info = before["result"]["result"]
        # Wait for *simulated* time to reach ``seconds`` (wall-clock bound as a safety net).
        sim_t = 0.0
        deadline = asyncio.get_running_loop().time() + seconds * 10 + 30
        await asyncio.sleep(min(seconds, 1.0))
        while asyncio.get_running_loop().time() < deadline:
            probe = await run_python(
                ctx,
                "gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()\n"
                "result = unreal.GameplayStatics.get_time_seconds(gw) if gw else -1.0\n",
            )
            sim_t = (
                float(probe.get("result", {}).get("result") or 0.0) if probe.get("success") else 0.0
            )
            if sim_t >= seconds or sim_t < 0:
                break
            await asyncio.sleep(min(0.5, max(0.1, seconds - sim_t)))
        after = await run_python(
            ctx,
            PRELUDE
            + _args(names=info["tracked"], stop=stop_after)
            + """
gw = UES.get_game_world()
sim_t = unreal.GameplayStatics.get_time_seconds(gw) if gw is not None else 0.0
end = {}
if gw is not None:
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_actor_label() in ARGS["names"]:
            end[a.get_actor_label()] = loc_list(a)
if ARGS["stop"]:
    LES.editor_request_end_play()
result = {"end": end, "sim_world": gw is not None, "simulated_seconds": round(sim_t, 3)}
""",
        )
        if not after.get("success"):
            return after
        stopped = await _wait_play_ended() if stop_after else False
        end = after["result"]["result"]["end"]
        report = []
        for name in info["tracked"]:
            s, e = info["start"].get(name), end.get(name)
            if not s or not e:
                report.append({"actor": name, "status": "missing after simulation"})
                continue
            moved = [round(b - a, 2) for a, b in zip(s["location"], e["location"], strict=True)]
            report.append(
                {
                    "actor": name,
                    "start": s["location"],
                    "end": e["location"],
                    "displacement": moved,
                    "distance": round(sum(m * m for m in moved) ** 0.5, 2),
                    "end_rotation": e["rotation"],
                }
            )
        return ok(
            {
                "seconds": seconds,
                "simulated_seconds": after["result"]["result"]["simulated_seconds"],
                "background_throttle_disabled": throttle_off,
                "sim_world": after["result"]["result"]["sim_world"],
                "actors": report,
                "stopped": stopped,
            }
        )
