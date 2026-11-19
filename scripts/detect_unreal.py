"""Detect installed Unreal Engine versions on Windows."""

from __future__ import annotations

import json
import os
from pathlib import Path


def launcher_installs() -> list[dict]:
    builds = []
    appdata = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    manifest = appdata / "Epic" / "UnrealEngineLauncher" / "LauncherInstalled.dat"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for item in data.get("InstallationList", []):
            if "UE_" in item.get("AppName", "") or item.get("AppName", "").startswith("UE"):
                builds.append({"name": item.get("AppName"), "path": item.get("InstallLocation")})
    # common paths
    for drive in ["C:", "D:", "E:"]:
        for p in (
            Path(f"{drive}/Program Files/Epic Games").glob("UE_*")
            if Path(f"{drive}/Program Files/Epic Games").exists()
            else []
        ):
            builds.append({"name": p.name, "path": str(p)})
    # dedupe
    seen = set()
    out = []
    for b in builds:
        key = str(b.get("path"))
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


def main():
    installs = launcher_installs()
    print(json.dumps({"installs": installs}, indent=2))
    return 0 if installs else 1


if __name__ == "__main__":
    raise SystemExit(main())
