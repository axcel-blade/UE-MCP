#!/usr/bin/env bash
# UnrealEngineMCP remote installer (macOS / Linux)
# Usage:
#   curl -LsSf https://axcel-blade.github.io/UE-MCP/install.sh | sh

set -euo pipefail

REPO_URL="https://github.com/axcel-blade/UE-MCP.git"
BRANCH="${UE_MCP_BRANCH:-develop}"
INSTALL_DIR="${UE_MCP_HOME:-$HOME/UE-MCP}"

echo "UnrealEngineMCP installer"
echo "Install dir: $INSTALL_DIR"
echo "Branch:      $BRANCH"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing clone..."
  cd "$INSTALL_DIR"
  git fetch origin
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  if [ -e "$INSTALL_DIR" ]; then
    echo "Directory exists but is not a git repo: $INSTALL_DIR" >&2
    echo "Set UE_MCP_HOME or remove it." >&2
    exit 1
  fi
  echo "Cloning $REPO_URL ($BRANCH)..."
  git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

uv sync

echo ""
echo "Next steps:"
echo "1. Install the plugin (Windows Editor primary):"
echo "   uv run python scripts/install_plugin.py --project \"/path/to/YourProject.uproject\""
echo "2. Open Unreal, enable UnrealEngineMCP (+ Editor Scripting Utilities), compile/restart"
echo "3. Confirm bridge on 127.0.0.1:55557"
echo "4. Configure your MCP client:"
echo "   uv run --directory \"$INSTALL_DIR\" unreal-engine-mcp"
echo "Done. Repo: $INSTALL_DIR"
