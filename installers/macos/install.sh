#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "UnrealEngineMCP installer (macOS)"

if ! command -v uv >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install uv
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

cd "$ROOT"
uv sync

echo "Python MCP server synced."
echo "Plugin compile is Windows-primary. On Windows:"
echo "  uv run python scripts/install_plugin.py --project \"/path/to/YourProject.uproject\""
echo "Configure your MCP client to run: uv run --directory \"$ROOT\" unreal-engine-mcp"
