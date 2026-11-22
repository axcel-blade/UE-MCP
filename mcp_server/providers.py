"""Online asset libraries (ported from Blender-MCP): Poly Haven, Poly Pizza, Sketchfab.

The MCP server and the editor normally run on the same machine, so the server
searches the provider, downloads files (HTTPS only, size-limited, no path traversal)
and hands Unreal local paths to import.
"""

from __future__ import annotations

import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import httpx

from mcp_server.config import ProvidersConfig
from mcp_server.exceptions import UnrealEngineMCPError

MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024
_SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]+")
POLYHAVEN = "https://api.polyhaven.com"
POLYPIZZA = "https://api.poly.pizza/v1"
SKETCHFAB = "https://api.sketchfab.com/v3"
# The Poly Haven API asks clients to identify themselves.
USER_AGENT = "unreal-engine-mcp"

POLYHAVEN_TEXTURE_MAPS = {
    "Diffuse": "base_color",
    "nor_gl": "normal",
    "Rough": "roughness",
    "Metal": "metallic",
    "AO": "ao",
}
POLYHAVEN_TYPES = {0: "hdris", 1: "textures", 2: "models"}
SOURCES = ("polyhaven", "polypizza", "sketchfab")


class ProviderError(UnrealEngineMCPError):
    def __init__(self, message: str, code: str = "provider_error") -> None:
        super().__init__(message, code=code)


def _client(timeout: float = 60.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT})


def asset_dir(cfg: ProvidersConfig, source: str, asset_id: str) -> Path:
    base = (
        Path(cfg.download_directory)
        if cfg.download_directory
        else Path(tempfile.gettempdir()) / "unreal_mcp_assets"
    )
    path = base / f"{source}_{_SAFE_ID.sub('_', asset_id)[:80]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_join(root: Path, relative: str) -> Path:
    """Join a provider-supplied relative path under ``root``, rejecting traversal."""
    rel = PurePosixPath(relative.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or not rel.parts or ":" in rel.parts[0]:
        raise ProviderError(f"Unsafe path in asset package: {relative!r}")
    target = (root / Path(*rel.parts)).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ProviderError(f"Unsafe path in asset package: {relative!r}")
    return target


async def fetch_file(
    client: httpx.AsyncClient, url: str, dest: Path, headers: dict[str, str] | None = None
) -> Path:
    if not url.startswith("https://"):
        raise ProviderError(f"Refusing non-HTTPS download URL: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    try:
        async with client.stream("GET", url, headers=headers, follow_redirects=True) as resp:
            resp.raise_for_status()
            with dest.open("wb") as out:
                async for chunk in resp.aiter_bytes():
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise ProviderError("Download exceeds the 500 MB limit")
                    out.write(chunk)
    except httpx.HTTPError as exc:
        dest.unlink(missing_ok=True)
        raise ProviderError(f"Download failed: {exc}") from exc
    except ProviderError:
        dest.unlink(missing_ok=True)
        raise
    return dest


def extract_zip(archive: Path, root: Path) -> Path:
    with zipfile.ZipFile(archive) as zf:
        if sum(i.file_size for i in zf.infolist()) > MAX_DOWNLOAD_BYTES * 2:
            raise ProviderError("Archive too large when extracted")
        for info in zf.infolist():
            target = safe_join(root, info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                dst.write(src.read())
    for pattern in ("*.glb", "*.gltf", "*.fbx", "*.obj", "*.usd*"):
        found = sorted(root.rglob(pattern))
        if found:
            return found[0]
    raise ProviderError("No importable model file found in download")


def _pick_res(node: Any, resolution: str) -> dict[str, Any] | None:
    if not isinstance(node, dict) or not node:
        return None
    if resolution in node:
        return node[resolution]

    def _key(k: str) -> int:
        digits = "".join(ch for ch in k if ch.isdigit())
        return int(digits) if digits else 9999

    return node[min(node, key=_key)]


def _normalize_ph_type(asset_type: str | None) -> str | None:
    if not asset_type:
        return None
    t = asset_type.lower().rstrip("s")
    return {"hdri": "hdris", "texture": "textures", "model": "models"}.get(t)


def provider_status(cfg: ProvidersConfig) -> dict[str, Any]:
    return {
        "polyhaven": {"enabled": cfg.polyhaven_enabled, "needs_key": False},
        "polypizza": {
            "enabled": cfg.polypizza_enabled,
            "configured": bool(cfg.polypizza_api_key),
        },
        "sketchfab": {
            "enabled": cfg.sketchfab_enabled,
            "configured": bool(cfg.sketchfab_api_token),
        },
    }


def _require(cfg: ProvidersConfig, source: str) -> None:
    if source not in SOURCES:
        raise ProviderError(f"source must be one of {', '.join(SOURCES)}", "invalid_params")
    if not getattr(cfg, f"{source}_enabled"):
        raise ProviderError(f"{source} is disabled in providers config", "permission_denied")
    if source == "polypizza" and not cfg.polypizza_api_key:
        raise ProviderError("Poly Pizza needs providers.polypizza_api_key", "permission_denied")
    if source == "sketchfab" and not cfg.sketchfab_api_token:
        raise ProviderError(
            "Sketchfab needs providers.sketchfab_api_token (or SKETCHFAB_API_TOKEN)",
            "permission_denied",
        )


async def search(
    cfg: ProvidersConfig, source: str, query: str, asset_type: str | None, limit: int
) -> list[dict[str, Any]]:
    _require(cfg, source)
    async with _client(30.0) as client:
        if source == "polyhaven":
            params = {"type": _normalize_ph_type(asset_type) or "all"}
            data = (await client.get(f"{POLYHAVEN}/assets", params=params)).raise_for_status()
            words = query.lower().split()
            out = []
            for asset_id, meta in data.json().items():
                hay = " ".join(
                    [
                        asset_id,
                        str(meta.get("name", "")),
                        " ".join(meta.get("tags", []) or []),
                        " ".join(meta.get("categories", []) or []),
                    ]
                ).lower()
                if all(w in hay for w in words):
                    out.append(
                        {
                            "id": asset_id,
                            "name": meta.get("name", asset_id),
                            "type": POLYHAVEN_TYPES.get(meta.get("type"), "models"),
                            "licence": "CC0",
                            "source": source,
                        }
                    )
                if len(out) >= limit:
                    break
            return out
        if source == "polypizza":
            resp = await client.get(
                f"{POLYPIZZA}/search/{query}",
                params={"Limit": str(limit)},
                headers={"x-auth-token": cfg.polypizza_api_key},
            )
            payload = resp.raise_for_status().json()
            items = payload if isinstance(payload, list) else payload.get("results", [])
            return [
                {
                    "id": i.get("ID") or i.get("id"),
                    "name": i.get("Title") or i.get("title"),
                    "licence": i.get("Licence") or i.get("license"),
                    "type": "models",
                    "source": source,
                }
                for i in items[:limit]
            ]
        resp = await client.get(
            f"{SKETCHFAB}/search",
            params={"type": "models", "q": query, "downloadable": "true", "count": str(limit)},
            headers={"Authorization": f"Token {cfg.sketchfab_api_token}"},
        )
        return [
            {
                "id": i.get("uid"),
                "name": i.get("name"),
                "licence": (i.get("license") or {}).get("label"),
                "type": "models",
                "source": source,
            }
            for i in resp.raise_for_status().json().get("results", [])[:limit]
        ]


async def download(
    cfg: ProvidersConfig, source: str, asset_id: str, asset_type: str | None, resolution: str
) -> dict[str, Any]:
    """Download an asset; returns {kind: model|texture|hdri, path|maps, licence}."""
    _require(cfg, source)
    out = asset_dir(cfg, source, asset_id)
    async with _client(180.0) as client:
        if source == "polyhaven":
            kind = _normalize_ph_type(asset_type)
            if kind is None:
                info = (await client.get(f"{POLYHAVEN}/info/{asset_id}")).raise_for_status()
                kind = POLYHAVEN_TYPES.get(info.json().get("type"), "models")
            files = (await client.get(f"{POLYHAVEN}/files/{asset_id}")).raise_for_status().json()
            if kind == "hdris":
                res = _pick_res(files.get("hdri", {}), resolution) or {}
                entry = res.get("hdr") or res.get("exr")
                if not entry:
                    raise ProviderError(f"No HDRI file for {asset_id}")
                dest = out / f"{asset_id}{Path(entry['url']).suffix}"
                return {"kind": "hdri", "path": str(await fetch_file(client, entry["url"], dest))}
            if kind == "textures":
                maps: dict[str, str] = {}
                for map_name, role in POLYHAVEN_TEXTURE_MAPS.items():
                    res = _pick_res(files.get(map_name, {}), resolution) or {}
                    entry = res.get("png") or res.get("jpg")
                    if entry:
                        dest = out / f"T_{asset_id}_{role}{Path(entry['url']).suffix}"
                        maps[role] = str(await fetch_file(client, entry["url"], dest))
                if "base_color" not in maps:
                    raise ProviderError(f"No diffuse map for texture {asset_id}")
                return {"kind": "texture", "maps": maps, "licence": "CC0"}
            res = _pick_res(files.get("gltf", {}), resolution) or {}
            gltf = res.get("gltf")
            if not gltf:
                raise ProviderError(f"No glTF package for model {asset_id}")
            main = await fetch_file(client, gltf["url"], out / f"{asset_id}.gltf")
            for rel, meta in (gltf.get("include") or {}).items():
                await fetch_file(client, meta["url"], safe_join(out, rel))
            return {"kind": "model", "path": str(main), "licence": "CC0"}
        if source == "polypizza":
            meta = (
                (
                    await client.get(
                        f"{POLYPIZZA}/model/{asset_id}",
                        headers={"x-auth-token": cfg.polypizza_api_key},
                    )
                )
                .raise_for_status()
                .json()
            )
            url = meta.get("Download") or meta.get("download")
            if not url:
                raise ProviderError("Poly Pizza returned no download URL")
            path = await fetch_file(client, url, out / f"{asset_id}.glb")
            return {
                "kind": "model",
                "path": str(path),
                "licence": meta.get("Licence") or meta.get("license"),
            }
        resp = await client.get(
            f"{SKETCHFAB}/models/{asset_id}/download",
            headers={"Authorization": f"Token {cfg.sketchfab_api_token}"},
        )
        if resp.status_code in (401, 403):
            raise ProviderError("Sketchfab refused the download (API token / downloadable?)")
        payload = resp.raise_for_status().json()
        # Signed URLs: do not forward the API token to the storage host.
        if (payload.get("glb") or {}).get("url"):
            path = await fetch_file(client, payload["glb"]["url"], out / f"{asset_id}.glb")
            return {"kind": "model", "path": str(path)}
        url = (payload.get("gltf") or {}).get("url")
        if not url:
            raise ProviderError("Sketchfab returned no glTF/GLB download")
        archive = await fetch_file(client, url, out / f"{asset_id}.zip")
        return {"kind": "model", "path": str(extract_zip(archive, out / "extracted"))}
