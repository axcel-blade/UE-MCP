"""End-to-end Windows installer helper (uses uv for Python deps)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    subprocess.check_call(cmd)


def require_uv() -> str:
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("uv is required. Install from https://docs.astral.sh/uv/ and re-run.")
    return uv


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="")
    args = ap.parse_args()

    uv = require_uv()
    run([uv, "sync", "--directory", str(ROOT)])
    run([uv, "run", "--directory", str(ROOT), "python", str(ROOT / "scripts" / "detect_unreal.py")])
    if args.project:
        run(
            [
                uv,
                "run",
                "--directory",
                str(ROOT),
                "python",
                str(ROOT / "scripts" / "install_plugin.py"),
                "--project",
                args.project,
            ]
        )
    run(
        [
            uv,
            "run",
            "--directory",
            str(ROOT),
            "python",
            str(ROOT / "scripts" / "configure_mcp.py"),
            "--client",
            "cursor",
        ]
    )
    print(
        "Install steps completed. Open Unreal, compile plugin, then run: "
        "uv run python scripts/test_connection.py"
    )


if __name__ == "__main__":
    main()
