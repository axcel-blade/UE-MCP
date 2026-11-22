"""Editor Python, visual feedback, guides and editor lifecycle (ported from Blender-MCP).

``unreal_execute_python`` is the primary escape hatch: anything the Unreal editor
Python API can do is reachable here. The rest of the tools in this module make that
practical for an AI client: ``unreal_look`` returns screenshots as images,
``unreal_lookup_api`` reads the live ``unreal`` module, ``unreal_get_guide`` serves
short workflow guides, ``unreal_search_scene`` finds actors, and
``unreal_open_editor`` / ``unreal_close_editor`` manage the editor process.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp.types import ImageContent, TextContent

from mcp_server.core.permissions import assert_tool_allowed
from mcp_server.core.python_exec import run_python
from mcp_server.core.response import fail, ok
from mcp_server.exceptions import UnrealEngineMCPError
from mcp_server.security.script_safety import check as safety_check

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext

LOOK_MODES = ("lit", "unlit", "wireframe", "detail_lighting", "lighting_only", "angles")
ANGLES = {
    "FRONT": (0.0, 180.0),
    "BACK": (0.0, 0.0),
    "LEFT": (0.0, 90.0),
    "RIGHT": (0.0, -90.0),
    "TOP": (-89.0, 0.0),
    "PERSPECTIVE": (-25.0, 225.0),
}


def list_guides() -> list[str]:
    return sorted(
        p.name[:-3]
        for p in resources.files("mcp_server.guides").iterdir()
        if p.name.endswith(".md")
    )


def read_guide(name: str) -> str:
    return resources.files("mcp_server.guides").joinpath(f"{name}.md").read_text("utf-8")


# ---------------------------------------------------------------------------------
# Editor discovery (open/close)
# ---------------------------------------------------------------------------------


def candidate_editors() -> list[str]:
    roots: list[Path] = []
    if sys.platform == "win32":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), r"D:\Program Files"):
            roots.append(Path(base) / "Epic Games")
        exe_rel = Path("Engine/Binaries/Win64/UnrealEditor.exe")
    elif sys.platform == "darwin":
        roots.append(Path("/Users/Shared/Epic Games"))
        exe_rel = Path("Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor")
    else:
        roots += [Path.home() / "UnrealEngine", Path("/opt/UnrealEngine")]
        exe_rel = Path("Engine/Binaries/Linux/UnrealEditor")
    found: list[str] = []
    for root in roots:
        if (root / exe_rel).is_file():
            found.append(str(root / exe_rel))
        if root.is_dir():
            for child in sorted(root.iterdir(), reverse=True):
                exe = child / exe_rel
                if child.name.startswith("UE_") and exe.is_file():
                    found.append(str(exe))
    return found


def find_editor(configured: str = "", version: str = "") -> str | None:
    if configured and Path(configured).is_file():
        return configured
    editors = candidate_editors()
    if version:
        editors = [e for e in editors if f"UE_{version}" in e]
    return editors[0] if editors else None


def editor_env() -> dict[str, str]:
    """Environment for the editor process.

    MCP clients often start servers with a trimmed environment (sometimes only PATH).
    Unreal needs the usual Windows profile variables during startup and exits early
    without them, so fill in any that are missing.
    """
    env = dict(os.environ)
    if sys.platform != "win32":
        return env
    home = env.get("USERPROFILE") or str(Path.home())
    defaults = {
        "SystemRoot": r"C:\Windows",
        "windir": env.get("SystemRoot", r"C:\Windows"),
        "SystemDrive": "C:",
        "USERPROFILE": home,
        "HOMEDRIVE": home[:2],
        "HOMEPATH": home[2:],
        "APPDATA": str(Path(home) / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(Path(home) / "AppData" / "Local"),
        "TEMP": str(Path(home) / "AppData" / "Local" / "Temp"),
        "TMP": str(Path(home) / "AppData" / "Local" / "Temp"),
        "ProgramFiles": r"C:\Program Files",
        "ProgramData": r"C:\ProgramData",
        "ComSpec": r"C:\Windows\System32\cmd.exe",
        "USERNAME": Path(home).name,
    }
    for key, value in defaults.items():
        env.setdefault(key, value)
    return env


def launch_detached_windows(exe: str, project: str) -> bool:
    """Start the editor via WMI Win32_Process.Create (outside this process's job)."""
    command = subprocess.list2cmdline([exe, project]).replace("'", "''")
    script = (
        "$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
        f"-Arguments @{{CommandLine='{command}'}}; exit $r.ReturnValue"
    )
    try:
        done = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            env=editor_env(),
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


def register(mcp: FastMCP, ctx: AppContext) -> None:
    settings = ctx.settings

    # -----------------------------------------------------------------------------
    # Python
    # -----------------------------------------------------------------------------

    @mcp.tool(name="unreal_execute_python")
    async def unreal_execute_python(
        code: str,
        confirmed: bool = False,
        preview_only: bool = False,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Run Python in the live Unreal Editor with the full ``unreal`` API. The most
        powerful tool: anything the editor can do through Python is reachable here
        (Sequencer, Movie Render Queue, Variant Manager, Datasmith, Niagara, PCG,
        World Partition, Control Rig, data tables, ...).

        ``unreal`` is preloaded. Returns the ``result`` variable if set, else the last
        expression's value, plus stdout and a traceback on error. Return dicts/lists.
        Batch related steps into one script and wrap edits in
        ``unreal.ScopedEditorTransaction`` so they can be undone. Read
        ``unreal_get_guide("unreal_python")`` first and use ``unreal_lookup_api`` when
        unsure of a class or property.

        Requires advanced security mode and ``security.allow_python_execution``. In
        ``confirmation`` mode pass ``confirmed=true`` (preview with
        ``preview_only=true``). Safe Python execution (on by default) refuses, before
        anything runs, scripts that start programs, delete files or assets, use the
        network, quit the editor, run console commands or use eval/exec/__import__.

        ``timeout``: seconds (default 60, max 3600). Not a secure sandbox.
        """
        try:
            assert_tool_allowed(settings, "unreal_execute_editor_python")
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        perm = settings.security.script_permission
        if perm == "restricted":
            return fail(
                "Script execution is restricted (security.script_permission=restricted). "
                "Use the dedicated tools or change the setting.",
                code="permission_denied",
            )
        if settings.security.safe_python_execution:
            violations = safety_check(code)
            if violations:
                lines = "; ".join(v.describe() for v in violations[:10])
                return fail(
                    f"Script refused by safe Python execution: {lines}. Do the work "
                    "without these operations (or with a dedicated tool), or ask the user "
                    "to set security.safe_python_execution=false.",
                    code="unsafe_script",
                    details={"violations": [v.describe() for v in violations]},
                )
        if preview_only:
            return ok({"preview_only": True, "code": code, "mode": perm})
        if perm == "confirmation" and not confirmed:
            return fail(
                "Script execution requires confirmed=true (script_permission=confirmation). "
                "Preview with preview_only=true, then re-run with confirmed=true.",
                code="confirmation_required",
            )
        return await run_python(ctx, code, timeout=timeout)

    @mcp.tool(name="unreal_execute_editor_python")
    async def unreal_execute_editor_python(
        code: str,
        confirmed: bool = False,
        preview_only: bool = False,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Alias of ``unreal_execute_python`` (same permission and safety checks)."""
        return await unreal_execute_python(code, confirmed, preview_only, timeout)

    @mcp.tool(name="unreal_lookup_api")
    async def unreal_lookup_api(query: str, limit: int = 40) -> dict[str, Any]:
        """Read the live Unreal Python API. ``query`` is a dotted name
        ("EditorActorSubsystem", "unreal.CineCameraComponent.focus_settings",
        "MoviePipelineQueueSubsystem") to get its doc and members, or search words
        ("variant set", "level sequence") to list matching names. Always matches the
        user's engine version and enabled plugins."""
        code = f"""
import inspect
q = {query!r}.strip()
limit = {int(limit)}
name = q[7:] if q.startswith("unreal.") else q
obj = unreal
ok_path = True
for part in [p for p in name.split(".") if p]:
    if hasattr(obj, part):
        obj = getattr(obj, part)
    else:
        ok_path = False
        break
if ok_path and name:
    doc = (inspect.getdoc(obj) or "")[:3000]
    members = []
    if inspect.isclass(obj) or inspect.ismodule(obj):
        for m in sorted(dir(obj)):
            if m.startswith("_"):
                continue
            try:
                mdoc = (inspect.getdoc(getattr(obj, m)) or "").split("\\n")[0][:160]
            except Exception:
                mdoc = ""
            members.append({{"name": m, "doc": mdoc}})
    result = {{"name": "unreal." + name, "kind": type(obj).__name__, "doc": doc,
              "members": members[:limit*4], "member_count": len(members)}}
else:
    words = [w.lower() for w in q.replace(".", " ").split() if w]
    hits = [n for n in dir(unreal) if all(w in n.lower() for w in words)]
    result = {{"query": q, "matches": sorted(hits)[:limit], "match_count": len(hits)}}
"""
        return await run_python(ctx, code)

    # -----------------------------------------------------------------------------
    # Guides
    # -----------------------------------------------------------------------------

    @mcp.tool(name="unreal_get_guide")
    async def unreal_get_guide(name: str = "") -> dict[str, Any]:
        """Short workflow guides. ``name``: unreal_python, games, film, live_events,
        automotive, simulation. Empty lists them."""
        guides = list_guides()
        if not name:
            return ok({"guides": guides})
        if name not in guides:
            return fail(f"Unknown guide '{name}'. Available: {', '.join(guides)}")
        return ok({"name": name, "text": read_guide(name)})

    # -----------------------------------------------------------------------------
    # Visual feedback
    # -----------------------------------------------------------------------------

    async def _capture(filename: str, max_size: int, view_mode: str = "") -> dict[str, Any]:
        params: dict[str, Any] = {"filename": filename, "max_size": max_size}
        if view_mode:
            params["view_mode"] = view_mode
        return await ctx.dispatcher.call("unreal_capture_viewport", params)

    def _text(value: Any) -> TextContent:
        return TextContent(type="text", text=value if isinstance(value, str) else json.dumps(value))

    def _images(shot: dict[str, Any]) -> list[Any]:
        result = shot.get("result") or {}
        data = result.get("image_base64")
        if not shot.get("success") or not data:
            return [_text(shot)]
        return [ImageContent(type="image", data=data, mimeType="image/png")]

    @mcp.tool(name="unreal_look")
    async def unreal_look(
        mode: str = "lit",
        angles: list[str] | None = None,
        focus: str = "",
        max_size: int = 768,
    ) -> list[Any]:
        """See the level. Use after every visible change, then fix what looks wrong.

        mode: lit (final look) | unlit (base colours) | wireframe | detail_lighting |
        lighting_only | angles (several views around the scene or ``focus`` actor in
        one call; ``angles`` defaults to FRONT, RIGHT, TOP, PERSPECTIVE).
        max_size: longest image edge in px. Images stay in context, so 384-512 is
        enough for layout checks.
        """
        mode = (mode or "lit").lower()
        if mode not in LOOK_MODES:
            return [_text(fail(f"mode must be one of {', '.join(LOOK_MODES)}"))]
        size = max(128, min(int(max_size), 2048))
        if mode != "angles":
            return _images(await _capture(f"look_{mode}", size, mode))

        wanted = [a.upper() for a in (angles or ["FRONT", "RIGHT", "TOP", "PERSPECTIVE"])]
        bad = [a for a in wanted if a not in ANGLES]
        if bad:
            return [_text(fail(f"Unknown angles {bad}; use {', '.join(ANGLES)}"))]
        # Frame the focus actor (or every visible mesh) and remember the user's view.
        frame = await run_python(
            ctx,
            f"""
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
focus = {focus!r}
actors = [a for a in eas.get_all_level_actors()
          if (a.get_actor_label() == focus if focus else isinstance(a, unreal.StaticMeshActor))]
lo = [1e18]*3; hi = [-1e18]*3
for a in actors:
    o, e = a.get_actor_bounds(False)
    for i, (c, x) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
        lo[i] = min(lo[i], c - x); hi[i] = max(hi[i], c + x)
if not actors:
    lo, hi = [-500]*3, [500]*3
loc, rot = ues.get_level_viewport_camera_info()
result = {{"center": [(l+h)/2 for l, h in zip(lo, hi)],
          "radius": max(100.0, max(h-l for l, h in zip(lo, hi))),
          "restore": [loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll]}}
""",
        )
        if not frame.get("success"):
            return [_text(frame)]
        info = frame["result"]["result"]
        cx, cy, cz = info["center"]
        dist = info["radius"] * 1.4
        out: list[Any] = []
        import math

        for name in wanted:
            pitch, yaw = ANGLES[name]
            p, y = math.radians(pitch), math.radians(yaw)
            x = cx - dist * math.cos(p) * math.cos(y)
            yy = cy - dist * math.cos(p) * math.sin(y)
            z = cz - dist * math.sin(p)
            await run_python(
                ctx,
                "unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)"
                f".set_level_viewport_camera_info(unreal.Vector({x}, {yy}, {z}), "
                f"unreal.Rotator(roll=0, pitch={pitch}, yaw={yaw}))",
            )
            out.append(_text(f"{name}:"))
            out.extend(_images(await _capture(f"look_{name.lower()}", size)))
        r = info["restore"]
        await run_python(
            ctx,
            "unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)"
            f".set_level_viewport_camera_info(unreal.Vector({r[0]}, {r[1]}, {r[2]}), "
            f"unreal.Rotator(roll={r[5]}, pitch={r[3]}, yaw={r[4]}))",
        )
        return out

    # -----------------------------------------------------------------------------
    # Scene search
    # -----------------------------------------------------------------------------

    @mcp.tool(name="unreal_search_scene")
    async def unreal_search_scene(
        query: str = "", actor_class: str = "", limit: int = 50
    ) -> dict[str, Any]:
        """Find actors by label/name substring and/or class (e.g. "PointLight",
        "StaticMeshActor", "CineCameraActor"). Returns label, class, location and
        attach parent; much cheaper than listing everything."""
        code = f"""
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
q = {query!r}.lower(); cls = {actor_class!r}.lower()
hits = []
for a in eas.get_all_level_actors():
    label = a.get_actor_label(); cname = a.get_class().get_name()
    if q and q not in label.lower() and q not in a.get_name().lower():
        continue
    if cls and cls not in cname.lower():
        continue
    l = a.get_actor_location(); p = a.get_attach_parent_actor()
    hits.append({{"label": label, "class": cname,
                 "location": [round(l.x, 1), round(l.y, 1), round(l.z, 1)],
                 "parent": p.get_actor_label() if p else ""}})
result = {{"count": len(hits), "actors": hits[:{int(limit)}]}}
"""
        return await run_python(ctx, code)

    # -----------------------------------------------------------------------------
    # Editor lifecycle
    # -----------------------------------------------------------------------------

    async def _bridge_up() -> bool:
        try:
            resp = await ctx.dispatcher.client.request("unreal_ping", {}, timeout=3, retry=False)
            return bool(resp.ok)
        except Exception:  # noqa: BLE001
            return False

    @mcp.tool(name="unreal_open_editor")
    async def unreal_open_editor(
        project: str = "",
        version: str = "",
        executable: str = "",
        wait: bool = True,
    ) -> dict[str, Any]:
        """Start the Unreal Editor with a .uproject and wait until the MCP bridge
        answers. ``project`` defaults to ``editor.project`` in config; ``version``
        picks an install (e.g. "5.8"); ``executable`` overrides detection."""
        if await _bridge_up():
            return ok({"already_running": True})
        project = project or settings.editor.project
        if not project or not Path(project).is_file():
            return fail("project must be the path to an existing .uproject file")
        exe = find_editor(executable or settings.editor.executable, version)
        if not exe:
            return fail(
                "Unreal Editor not found; pass executable= or set editor.executable",
                details={"searched": candidate_editors()},
            )
        # Detach fully: no inherited stdio (the MCP server's stdin/stdout is the
        # protocol pipe), own process group, and outside the launcher's job object so
        # the editor outlives this server.
        common: dict[str, Any] = {
            "env": editor_env(),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            # Launchers such as `uv run` put the server in a job object that kills its
            # children when the server exits and forbids breakaway. Creating the editor
            # through WMI puts it outside any job, with the user's normal environment.
            launched = await asyncio.to_thread(launch_detached_windows, exe, project)
            if not launched:
                flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                subprocess.Popen(  # noqa: ASYNC220 - detached launch, returns immediately
                    [exe, project], creationflags=flags, **common
                )
        else:
            subprocess.Popen(  # noqa: ASYNC220
                [exe, project], start_new_session=True, **common
            )
        if not wait:
            return ok({"started": True, "executable": exe, "project": project})
        deadline = asyncio.get_running_loop().time() + settings.editor.startup_timeout
        while asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(5)
            if await _bridge_up():
                return ok({"started": True, "ready": True, "executable": exe})
        return fail(
            "Editor started but the MCP bridge did not answer before the timeout; "
            "check that the UnrealEngineMCP plugin is enabled in the project.",
            code="timeout",
        )

    @mcp.tool(name="unreal_close_editor")
    async def unreal_close_editor(save: bool = False, confirmed: bool = False) -> dict[str, Any]:
        """Quit the editor. ``save=true`` saves dirty packages first (untitled maps are
        skipped). Unsaved work is lost otherwise, so this needs ``confirmed=true``."""
        if not confirmed:
            return fail(
                "Closing the editor discards unsaved work. Pass confirmed=true "
                "(and save=true to save first).",
                code="permission_denied",
            )
        saved = await ctx.dispatcher.call("unreal_save_all", {}) if save else None
        await run_python(ctx, "unreal.SystemLibrary.quit_editor()")
        return ok({"closing": True, "saved": saved})
