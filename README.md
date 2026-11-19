# Unreal Engine MCP

[![CI](https://github.com/axcel-blade/UE-MCP/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/axcel-blade/UE-MCP/actions/workflows/ci.yml)
[![CD](https://github.com/axcel-blade/UE-MCP/actions/workflows/cd.yml/badge.svg)](https://github.com/axcel-blade/UE-MCP/actions/workflows/cd.yml)
[![Pages](https://github.com/axcel-blade/UE-MCP/actions/workflows/pages.yml/badge.svg?branch=develop)](https://github.com/axcel-blade/UE-MCP/actions/workflows/pages.yml)
[![Release](https://github.com/axcel-blade/UE-MCP/actions/workflows/release.yml/badge.svg)](https://github.com/axcel-blade/UE-MCP/actions/workflows/release.yml)
[![Latest release](https://img.shields.io/github/v/release/axcel-blade/UE-MCP?display_name=tag&logo=github)](https://github.com/axcel-blade/UE-MCP/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-c4f82a)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/packaging-uv-DE5FE9?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.3%2B-0E1128?logo=unrealengine&logoColor=white)](https://www.unrealengine.com/)
[![MCP](https://img.shields.io/badge/protocol-MCP-555)](docs/ARCHITECTURE.md)
[![Local only](https://img.shields.io/badge/bridge-localhost%20default-555)](SECURITY.md)

Production-oriented **Model Context Protocol (MCP)** integration for **Unreal Engine 5**. AI clients (Claude Desktop, Cursor, VS Code, Codex, Windsurf, and others) can inspect projects, spawn and edit actors, manage levels/assets/Blueprints, capture viewports, and automate Editor workflows through a local bridge.

This project is **not** affiliated with Epic Games.

## Features

- MCP stdio server + Unreal Editor C++ plugin TCP bridge (localhost by default)
- Length-prefixed JSON protocol with GameThread-safe execution
- Actor, level, asset, Blueprint, material, lighting, and viewport tools
- Scene intelligence helpers and high-level workflows (`unreal_create_room`, `unreal_setup_lighting`, …)
- Safe / Advanced security modes; destructive actions require confirmation
- Optional bridge auth token; Blender→Unreal FBX import validation helpers
- uv-based Python toolchain with CI, CD, Pages, and Release GitHub Actions

See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for honest coverage of implemented vs `unsupported` tools.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (required)
- Python 3.11+
- Unreal Engine 5.3+ with **Editor Scripting Utilities**
- Windows 10/11 (primary); Visual Studio 2022 or Rider to compile the plugin

## Quick start

Install site (Astro / GitHub Pages): [axcel-blade.github.io/UE-MCP](https://axcel-blade.github.io/UE-MCP/)

**Windows (PowerShell)** — one liner:

```powershell
irm https://axcel-blade.github.io/UE-MCP/install.ps1 | iex
```

**macOS / Linux:**

```bash
curl -LsSf https://axcel-blade.github.io/UE-MCP/install.sh | sh
```

Or from a local clone with uv:

```powershell
uv sync
uv run python scripts/install_plugin.py --project "D:\Path\To\YourProject.uproject"
```

1. Open the Unreal project → enable **Unreal Engine MCP** (+ Editor Scripting Utilities) → compile / restart
2. Confirm Output Log: bridge listening on `127.0.0.1:55557`
3. Point your MCP client at:

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

Smoke test:

```powershell
uv run python scripts/test_connection.py
```

More client samples: [config/mcp_clients/](config/mcp_clients/). Full install guide: [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Install & MCP client setup |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Config & environment |
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | First workflow |
| [docs/COMMUNICATION_PROTOCOL.md](docs/COMMUNICATION_PROTOCOL.md) | Wire protocol |
| [docs/MCP_TOOLS.md](docs/MCP_TOOLS.md) | MCP tools overview |
| [docs/MCP_RESOURCES.md](docs/MCP_RESOURCES.md) | MCP resources |
| [docs/MCP_PROMPTS.md](docs/MCP_PROMPTS.md) | MCP prompts |
| [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md) | Safe / Advanced mode controls |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common failures |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Developer guide |
| [docs/TESTING.md](docs/TESTING.md) | Test strategy |
| [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) | Engine / client compatibility |
| [docs/GIT_FLOW.md](docs/GIT_FLOW.md) | Branching model |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Engineering decision log |
| [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) | Feature status |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Git Flow & contribution guide |
| [SUPPORT.md](SUPPORT.md) | How to get help |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [LICENSE](LICENSE) | MIT license |

## Architecture

```text
AI Client --stdio MCP--> unreal-engine-mcp --TCP length-prefixed JSON--> Unreal Engine MCP plugin --Editor APIs--> Unreal Engine
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Architectural reference: [Blender-MCP](https://github.com/axcel-blade/Blender-MCP) (patterns adapted for Unreal; not a code copy). Also evaluated: IvanMurzak/Unreal-MCP, flopperam/unreal-engine-mcp, tahooki/unreal-blender-mcp.

## Git Flow

| Branch | Purpose |
|--------|---------|
| `main` | Production releases |
| `develop` | Integration |
| `feature/*` | Features → `develop` |
| `release/*` | Release prep → `main` + `develop` |
| `hotfix/*` | Urgent fixes from `main` |

Details: [CONTRIBUTING.md](CONTRIBUTING.md) · [docs/GIT_FLOW.md](docs/GIT_FLOW.md).

### CI / CD / Pages / Release

| Workflow | When | What |
|----------|------|------|
| [CI](.github/workflows/ci.yml) | Push/PR on Git Flow branches | uv lint, pytest (3.11–3.13), plugin layout check |
| [Pages](.github/workflows/pages.yml) | Push to `develop`/`main` touching `site/**`, or manual | Build Astro site; deploy GitHub Pages from `main` only |
| [Release](.github/workflows/release.yml) | Manual dispatch (from `main`) | Version bump, CHANGELOG, tag `v*`, GitHub Release, dispatch CD |
| [CD](.github/workflows/cd.yml) | Tag `v*` / Release dispatch | Build wheels, pack plugin zip, attach assets, optional PyPI, refresh Pages |

`main` and `develop` are branch-protected (PR + review). Details: [docs/GIT_FLOW.md](docs/GIT_FLOW.md).

## Security

- Bridge binds to `127.0.0.1` by default
- Optional shared auth token
- Default **Safe** mode restricts script/console execution and gates destructive tools with `confirmed=true`
- `unreal_execute_editor_python` / console commands require Advanced mode + explicit config flags — they are **not a sandbox**

Report vulnerabilities privately via [SECURITY.md](SECURITY.md). Product controls: [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md).

## Development

This project is managed exclusively with **uv** (lockfile + virtualenv).

```powershell
uv sync
uv run pytest
uv run ruff check mcp_server tests scripts
uv run unreal-engine-mcp
```

Diagnose a live Unreal connection:

```powershell
uv run python scripts/diagnose.py
uv run python scripts/test_connection.py
```

Plugin sources: `UnrealEngineMCP/Source/UnrealEngineMCP/`.

## License

MIT © AXCEL BLADE — see [LICENSE](LICENSE).

Unreal® is a trademark of Epic Games, Inc. This project is not affiliated with or endorsed by Epic Games.
