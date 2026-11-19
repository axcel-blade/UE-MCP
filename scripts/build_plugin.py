"""Invoke RunUAT BuildPlugin when engine path is known."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--engine", required=True, help="UE root, e.g. C:/Program Files/Epic Games/UE_5.4"
    )
    ap.add_argument("--output", default=str(Path("Build/UnrealEngineMCPPlugin")))
    args = ap.parse_args()
    uat = Path(args.engine) / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
    plugin = Path(__file__).resolve().parents[1] / "UnrealEngineMCP" / "UnrealEngineMCP.uplugin"
    if not uat.is_file():
        raise SystemExit(f"RunUAT not found: {uat}")
    cmd = [
        str(uat),
        "BuildPlugin",
        f"-Plugin={plugin}",
        f"-Package={Path(args.output).resolve()}",
        "-Rocket",
    ]
    print(">", " ".join(cmd))
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
