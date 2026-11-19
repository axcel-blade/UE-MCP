# Contributing

Thanks for contributing to **Unreal Engine MCP**.

## Git Flow

This repository uses Git Flow:

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready releases only |
| `develop` | Integration branch for the next release |
| `feature/*` | New features (branch from `develop`) |
| `release/*` | Release preparation (branch from `develop`) |
| `hotfix/*` | Urgent production fixes (branch from `main`) |

See [docs/GIT_FLOW.md](docs/GIT_FLOW.md) for the full branching model.

`main` and `develop` are **branch-protected**: open a PR (1 approving review, conversation resolution required). Do not force-push those branches.

### Feature workflow

```powershell
git checkout develop
git pull origin develop
git checkout -b feature/short-description
# ... work ...
uv sync
uv run pytest
uv run ruff check mcp_server tests scripts
git push -u origin HEAD
```

Open a pull request into **`develop`**.

### Release workflow

```powershell
git checkout develop
git checkout -b release/x.y.z
# bump version, update CHANGELOG.md, final fixes
# merge to main (tag) and back to develop
```

Preferred: run the **Release** GitHub Action (`.github/workflows/release.yml`):

1. Choose branch `main`
2. Enter version without `v` (e.g. `0.1.1`)
3. Workflow bumps versions, updates `CHANGELOG.md`, tags `vX.Y.Z`, creates the GitHub Release, then dispatches **CD**

### Hotfix workflow

```powershell
git checkout main
git checkout -b hotfix/short-description
# fix, test, update CHANGELOG.md
# PR into main and develop
```

## Tooling

- Use **uv** only (`uv sync`, `uv run`)
- Python **3.11+**
- Site changes: `cd site && pnpm install && pnpm build` (keep `site/public/install.ps1` UTF-8 **without BOM**)
- Before opening a PR:

```powershell
uv sync
uv run pytest
uv run ruff check mcp_server tests scripts
uv run ruff format --check mcp_server tests scripts
```

## Code guidelines

- Prefer real Unreal Editor API integration over placeholders
- Never return fake success for unimplemented tools — use structured `unsupported` errors
- Keep C++ engine work on the Game Thread
- Keep documentation synchronized with actual capabilities (`docs/IMPLEMENTATION_STATUS.md`)
- Do not commit secrets, auth tokens, or local project paths

## Pull requests

- Use the PR template
- Target `develop` for features; `main` for hotfixes/releases as appropriate
- Link related issues

## Reporting issues

Use GitHub Issues with the provided templates. For vulnerabilities, follow [SECURITY.md](SECURITY.md).
