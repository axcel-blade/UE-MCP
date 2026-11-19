# Development

## Layout

- `mcp_server/` — Python MCP server (FastMCP / STDIO)
- `UnrealEngineMCP/` — UE Editor C++ plugin (TCP bridge + tools)
- `scripts/` — install / diagnostics helpers
- `installers/` — OS installers for a local clone
- `site/` — Astro + pnpm GitHub Pages install site
- `tests/` — pytest
- `docs/` — documentation
- `.github/workflows/` — CI, CD, Pages, Release

## Python toolchain

This project uses [uv](https://docs.astral.sh/uv/):

```powershell
uv sync
uv run pytest
uv run ruff check mcp_server tests scripts
uv run unreal-engine-mcp
```

`uv.lock` is the source of truth for dependency versions.

## Site (Astro)

```powershell
cd site
pnpm install
pnpm dev      # http://localhost:4321 with ASTRO_BASE from env / config
pnpm build
```

Installer scripts under `site/public/` must stay **UTF-8 without BOM** (PowerShell 5.1 / `irm | iex`).

## Adding a tool

1. Implement C++ handler and register in the appropriate `*Tools.cpp`.
2. Add Python tool wrapper (or rely on category generator pattern).
3. Update docs and [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).
4. Add unit/integration coverage where possible.

## Git Flow

See [GIT_FLOW.md](GIT_FLOW.md) and [CONTRIBUTING.md](../CONTRIBUTING.md). `main` and `develop` are branch-protected; open PRs from `feature/*` / `release/*` / `hotfix/*`.
