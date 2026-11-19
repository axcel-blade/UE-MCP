#!/usr/bin/env python3
"""Copy UnrealEngineMCP plugin into a project Plugins folder."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="Path to .uproject")
    args = ap.parse_args()
    project = Path(args.project).resolve()
    if project.suffix.lower() != ".uproject" or not project.is_file():
        raise SystemExit(f"Invalid project: {project}")
    src = Path(__file__).resolve().parents[1] / "UnrealEngineMCP"
    dst = project.parent / "Plugins" / "UnrealEngineMCP"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        backup = dst.with_name(f"UnrealEngineMCP.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.move(str(dst), str(backup))
        print(f"Backed up existing plugin to {backup}")
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("Binaries", "Intermediate", "Saved"))
    print(f"Installed plugin to {dst}")
    print("Next: regenerate project files and compile the Editor target.")


if __name__ == "__main__":
    main()
