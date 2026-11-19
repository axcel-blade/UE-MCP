#!/usr/bin/env python3
"""Generate MCP client configs that launch the server via uv."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_POSIX = str(ROOT).replace("\\", "/")
UV = shutil.which("uv") or "uv"

TEMPLATES = {
    "cursor": {
        "mcpServers": {
            "unreal-engine-mcp": {
                "command": UV,
                "args": ["run", "--directory", ROOT_POSIX, "unreal-engine-mcp"],
                "env": {
                    "UNREAL_ENGINE_MCP_HOST": "127.0.0.1",
                    "UNREAL_ENGINE_MCP_PORT": "55557",
                    "UNREAL_ENGINE_MCP_SECURITY_MODE": "safe",
                },
            }
        }
    },
    "claude_desktop": {
        "mcpServers": {
            "unreal-engine-mcp": {
                "command": UV,
                "args": ["run", "--directory", ROOT_POSIX, "unreal-engine-mcp"],
                "env": {
                    "UNREAL_ENGINE_MCP_HOST": "127.0.0.1",
                    "UNREAL_ENGINE_MCP_PORT": "55557",
                },
            }
        }
    },
    "vscode": {
        "servers": {
            "unreal-engine-mcp": {
                "type": "stdio",
                "command": UV,
                "args": ["run", "--directory", ROOT_POSIX, "unreal-engine-mcp"],
            }
        }
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", choices=sorted(TEMPLATES), default="cursor")
    args = ap.parse_args()
    out = ROOT / "config" / "mcp_clients" / f"{args.client}.generated.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(TEMPLATES[args.client], indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
