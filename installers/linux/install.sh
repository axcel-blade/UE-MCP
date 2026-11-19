#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "UnrealEngineMCP installer (Linux)"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

cd "$ROOT"
uv sync

echo "Python MCP server synced."
echo "Plugin compile is Windows-primary. On Windows:"
echo "  uv run python scripts/install_plugin.py --project \"/path/to/YourProject.uproject\""
echo "Configure your MCP client to run: uv run --directory \"$ROOT\" unreal-engine-mcp"
