# Installation

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installed automatically by the remote installer)
- Git
- Python 3.11+ (uv can install/manage it)
- Unreal Engine 5.3+ with **Editor Scripting Utilities**
- Windows 10/11 (primary) for Editor plugin compile; Visual Studio 2022 or Rider

Do **not** use `pip install` for this project. Use `uv sync` / `uv run`.

## One-line install (GitHub Pages)

Site: [https://axcel-blade.github.io/UE-MCP/](https://axcel-blade.github.io/UE-MCP/)

**Windows (PowerShell):**

```powershell
irm https://axcel-blade.github.io/UE-MCP/install.ps1 | iex
```

**macOS / Linux:**

```bash
curl -LsSf https://axcel-blade.github.io/UE-MCP/install.sh | sh
```

This clones into `~/UE-MCP` (override with `UE_MCP_HOME`), checks out `develop` (override with `UE_MCP_BRANCH`), runs `uv sync`, and updates Cursor / Claude Desktop MCP config when those files already exist.

Then install the Editor plugin into your Unreal project (see below).

## Local clone install

### Windows

```powershell
.\installers\windows\install.ps1
```

Manual:

```powershell
uv sync
uv run python scripts/install_plugin.py --project "D:\Path\To\YourProject.uproject"
uv run python scripts/configure_mcp.py --client cursor
```

### Linux / macOS

```bash
chmod +x installers/linux/install.sh installers/macos/install.sh
./installers/linux/install.sh   # or macos
```

These sync the Python MCP server. Plugin compile is Windows-primary.

Manual:

```bash
uv sync
uv run python scripts/install_plugin.py --project "/path/to/YourProject.uproject"
```

## Automated helper (Windows)

```powershell
uv sync
uv run python scripts/detect_unreal.py
uv run python scripts/install.py --project "D:\Games\MyProject\MyProject.uproject"
uv run python scripts/configure_mcp.py --client cursor
uv run python scripts/test_connection.py
```

`install.py` will:

1. Run `uv sync` for Python dependencies
2. Detect Unreal installations (registry / Epic Launcher paths)
3. Copy the plugin into the project `Plugins/` folder (with backup if present)
4. Write MCP client config snippets that launch via `uv run`
5. Prompt you to smoke-test once the Editor bridge is running

## Manual plugin install

1. Copy `UnrealEngineMCP/` → `<Project>/Plugins/UnrealEngineMCP/`
2. Right-click `.uproject` → Generate Visual Studio project files
3. Build the Editor target
4. Enable **Unreal Engine MCP** (+ Editor Scripting Utilities) and restart
5. Confirm Output Log: bridge listening on `127.0.0.1:55557`

Or download `UnrealEngineMCP-plugin-*.zip` from the [latest GitHub Release](https://github.com/axcel-blade/UE-MCP/releases/latest) when available.

## MCP clients

Configure an `unreal-engine-mcp` server entry that runs:

```bash
uv run --directory /path/to/UE-MCP unreal-engine-mcp
```

Example:

```json
{
  "mcpServers": {
    "unreal-engine-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:/path/to/UE-MCP",
        "unreal-engine-mcp"
      ],
      "env": {
        "UNREAL_ENGINE_MCP_HOST": "127.0.0.1",
        "UNREAL_ENGINE_MCP_PORT": "55557",
        "UNREAL_ENGINE_MCP_SECURITY_MODE": "safe"
      }
    }
  }
}
```

More samples: [config/mcp_clients/](../config/mcp_clients/). Fully quit and reopen the client after editing MCP config.

## Uninstall

```powershell
uv run python scripts/uninstall.py --project "D:\Games\MyProject\MyProject.uproject"
```

## Enabling GitHub Pages (maintainers)

1. Repo **Settings → Pages**
2. **Source**: GitHub Actions
3. Set the repository **Website** to `https://axcel-blade.github.io/UE-MCP/`
4. Push to `develop` or `main` (or run the **Pages** workflow manually)

The site is an **Astro** app in `site/` managed with **pnpm**. The Pages workflow runs `pnpm install --frozen-lockfile && pnpm build` and deploys `site/dist`.

Local preview:

```bash
cd site
pnpm install
pnpm dev
```

### Docker

Production-like static image (nginx on port 8080):

```bash
cd site
docker compose up --build
# http://localhost:8080/
# http://localhost:8080/install.ps1
```

Dev server with hot reload:

```bash
cd site
docker compose -f docker-compose.dev.yml up --build
# http://localhost:4321/
```

Build args (optional):

```bash
docker build \
  --build-arg ASTRO_SITE=https://axcel-blade.github.io \
  --build-arg ASTRO_BASE=/UE-MCP \
  -t unreal-engine-mcp-site \
  .
```
