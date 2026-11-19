"""STDIO entrypoint for MCP clients."""

from __future__ import annotations

from mcp_server.config import load_settings
from mcp_server.server import create_server


def main() -> None:
    settings = load_settings()
    mcp = create_server(settings)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
