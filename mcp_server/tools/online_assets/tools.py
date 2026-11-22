"""Search and import assets from online libraries (ported from Blender-MCP)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp_server import providers
from mcp_server.core.python_exec import run_python
from mcp_server.core.response import fail, ok
from mcp_server.exceptions import UnrealEngineMCPError
from mcp_server.tools.industries.tools import PRELUDE, _args

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from mcp_server.server import AppContext


IMPORT_TEMPLATE = r"""
def import_files(files, dest):
    ensure_dir(dest)
    tasks = []
    for f in files:
        t = unreal.AssetImportTask()
        t.filename = f; t.destination_path = dest
        t.automated = True; t.replace_existing = True; t.save = True
        tasks.append(t)
    AT.import_asset_tasks(tasks)
    out = []
    for t in tasks:
        out.extend(list(t.imported_object_paths or []))
    return out

kind = ARGS["kind"]; dest = ARGS["dest"]; placed = []
if kind == "model":
    paths = import_files([ARGS["path"]], dest)
    meshes = [p for p in paths if isinstance(unreal.load_asset(p), (unreal.StaticMesh, unreal.SkeletalMesh))]
    if ARGS["place"]:
        for p in meshes:
            a = EAS.spawn_actor_from_object(unreal.load_asset(p), V(ARGS["location"]))
            if ARGS["label"]:
                a.set_actor_label(ARGS["label"])
            placed.append(a.get_actor_label())
    result = {"kind": kind, "imported": paths[:50], "meshes": meshes, "placed": placed}
elif kind == "texture":
    paths = import_files(list(ARGS["maps"].values()), dest)
    result = {"kind": kind, "textures": paths}
else:
    paths = import_files([ARGS["path"]], dest)
    cube = next((unreal.load_asset(p) for p in paths if isinstance(unreal.load_asset(p), unreal.TextureCube)), None)
    if cube is None:
        raise RuntimeError("HDRI did not import as a cubemap: %s" % paths)
    sky = None
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.SkyLight):
            sky = a
    if sky is None:
        sky = spawn(unreal.SkyLight, "HDRI_SkyLight", (0, 0, 500))
    lc = sky.light_component
    lc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    lc.set_editor_property("cubemap", cube)
    lc.recapture_sky()
    result = {"kind": kind, "cubemap": cube.get_path_name(), "sky_light": sky.get_actor_label()}
"""


def register(mcp: FastMCP, ctx: AppContext) -> None:
    cfg = ctx.settings.providers

    @mcp.tool(name="unreal_search_online_assets")
    async def unreal_search_online_assets(
        query: str,
        source: str = "polyhaven",
        asset_type: str = "",
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search free online asset libraries. ``source``: polyhaven (CC0 models,
        textures, HDRIs; no key), polypizza (low-poly models; needs
        providers.polypizza_api_key), sketchfab (needs providers.sketchfab_api_token).
        ``asset_type`` (Poly Haven): models, textures or hdris. Import a result with
        ``unreal_import_online_asset``."""
        try:
            results = await providers.search(cfg, source, query, asset_type or None, limit)
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        except Exception as exc:  # noqa: BLE001
            return fail(f"{source} search failed: {exc}", code="provider_error")
        return ok(
            {"source": source, "results": results, "providers": providers.provider_status(cfg)}
        )

    @mcp.tool(name="unreal_import_online_asset")
    async def unreal_import_online_asset(
        asset_id: str,
        source: str = "polyhaven",
        asset_type: str = "",
        resolution: str = "1k",
        destination: str = "",
        place_in_level: bool = True,
        location: dict[str, float] | None = None,
        label: str = "",
    ) -> dict[str, Any]:
        """Download an asset found with ``unreal_search_online_assets`` and import it.
        Models become Static/Skeletal Meshes (placed in the level unless
        ``place_in_level=false``), texture sets become Texture2D assets, HDRIs become a
        cubemap assigned to the level's Sky Light. Imported/arrived scale varies; check
        with ``unreal_measure``."""
        try:
            got = await providers.download(cfg, source, asset_id, asset_type or None, resolution)
        except UnrealEngineMCPError as exc:
            return fail(exc.message, code=exc.code)
        except Exception as exc:  # noqa: BLE001
            return fail(f"{source} download failed: {exc}", code="provider_error")
        dest = destination or f"/Game/Online/{source}/{asset_id.replace('-', '_')}"
        code = (
            PRELUDE
            + _args(
                kind=got["kind"],
                path=got.get("path", ""),
                maps=got.get("maps", {}),
                dest=dest,
                place=place_in_level,
                location=location,
                label=label,
            )
            + IMPORT_TEMPLATE
        )
        res = await run_python(ctx, code, timeout=600)
        if res.get("success"):
            res["result"]["licence"] = got.get("licence")
            res["result"]["source"] = source
        return res
