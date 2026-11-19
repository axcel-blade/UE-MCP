# Git Flow

Unreal Engine MCP uses classic Git Flow.

```text
main ─────●────────────●────────────●─────  production tags (vX.Y.Z)
           \          /            /
            \        / hotfix/*   /
             \      /            /
develop ──────●────●────●───────●─────────  integration
               \  /      \
                \/        \ release/*
           feature/*
```

## Branches

| Branch | Created from | Merges into | Purpose |
|--------|--------------|-------------|---------|
| `main` | — | — | Stable releases only |
| `develop` | `main` | `main` (via release) | Ongoing integration |
| `feature/*` | `develop` | `develop` | Features / non-urgent fixes |
| `release/*` | `develop` | `main` + `develop` | Release hardening / version bump |
| `hotfix/*` | `main` | `main` + `develop` | Urgent production fixes |

## Naming examples

- `feature/unreal-engine-mcp-foundation`
- `feature/blueprint-node-wiring`
- `release/0.2.0`
- `hotfix/tcp-auth-token-check`

## Branch protection

`main` and `develop` are protected on GitHub (aligned with Blender-MCP):

- Pull request required (1 approving review)
- Stale reviews dismissed on new pushes
- Conversation resolution required
- Force pushes and branch deletions blocked

Work on `feature/*`, `release/*`, and `hotfix/*`, then open a PR into `develop` or `main`.

## CI triggers

- **CI** runs on pushes to `main`, `develop`, `feature/**`, `release/**`, `hotfix/**` and on PRs into `main` / `develop`
- **Pages** builds the Astro install site on `develop` / `main` when `site/**` changes; deploys to GitHub Pages from `main` only
- **Release** is manually dispatched (preferred from `main`)
- **CD** runs on `v*` tags (or via Release dispatch)

## Cutting a release

1. Ensure `develop` is green
2. Open / finalize `release/x.y.z` if needed, then merge to `main`
3. Run Actions → **Release** with version `x.y.z` on `main`
4. Merge release/hotfix back into `develop`
