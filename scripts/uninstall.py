#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    plugin = Path(args.project).resolve().parent / "Plugins" / "UnrealEngineMCP"
    if plugin.exists():
        shutil.rmtree(plugin)
        print(f"Removed {plugin}")
    else:
        print("Plugin not found")


if __name__ == "__main__":
    main()
