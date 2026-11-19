# Implementation Status

Last updated: 2026-11-19  
Branch: `feature/unreal-engine-mcp-foundation`

## Summary

Unreal Engine MCP is being built as a Blender-MCP-style three-layer system:

1. Python FastMCP server (`mcp_server/`) over STDIO  
2. Length-prefixed JSON TCP bridge  
3. C++ Unreal Editor plugin (`UnrealEngineMCP/`)

## Repo operations

| Area | Status |
|---|---|
| Git Flow (`main` / `develop` / `feature/*` / `release/*` / `hotfix/*`) | Documented |
| Branch protection (`main`, `develop`) | Enabled on GitHub |
| GitHub community markdown (uppercase) | Added |
| CI / CD / Release workflows | Added (`.github/workflows/`) |
| Pages workflow + Astro site (`site/`) | Added; builds on `develop`/`main`, deploys from `main` |
| Remote / local installers (`site/public`, `installers/`) | Added (UTF-8 no BOM for PowerShell) |
| GitHub About website | `https://axcel-blade.github.io/UE-MCP/` |

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 1 Foundation | **Implemented in code** | Plugin bridge, protocol, MCP server, health tools |
| 2 Core editor tools | **Implemented in code** | Actors, levels, assets, transforms, inspection |
| 3 Advanced editor tools | **In progress** | Blueprint/material/lighting/rendering handlers landing |
| 4 Creative tools | **Partial** | Registered on Python side; C++ returns `unsupported` until real handlers land |
| 5 Intelligence | **Partial** | Scene stats/hierarchy designed; full analyzers landing |
| 6 Production readiness | **In progress** | Docs, scripts, unit tests; UE compile verification requires local UE install |

## Verified locally (this machine)

| Check | Result |
|---|---|
| Python package imports / unit tests | **Passed** — `pytest` 6 passed (protocol, permissions, config) |
| MCP server factory | **Passed** — `create_server()` loads and registers tools |
| Unreal plugin compile | **Not executed** — requires Unreal Engine + UBT on this machine |
| Live Editor integration | **Not executed** — needs Editor with plugin loaded |
| End-to-end actor spawn | **Not executed** |

Do not treat unchecked items as passing.

## Python MCP tools

All listed MCP tools are registered and forward to the Unreal bridge. Success depends on C++ handler availability.

## C++ handlers

| Family | Status |
|---|---|
| System | Implemented |
| Actors | Implemented |
| Levels | Implemented |
| Assets | Implemented (+ Blender FBX helpers) |
| Blueprints | Implemented (core create/compile/vars/nodes; macros limited) |
| Materials | Implemented (create/instance/params/assign; graph expr unsupported) |
| Lighting | Implemented |
| Rendering | Implemented (viewport capture/camera; offline render limited) |
| Project / testing | Implemented (diagnostics/save/console; python/build unsupported) |
| Intelligence | Implemented (bounded analyzers) |
| Physics | Partial (simulate/collision/mass/gravity) |
| Animation / Niagara / UMG / Sequencer / Meshes | Stubbed as `unsupported` until implemented |
| Gameplay domain C++ | Not yet registered (Python forwards; plugin returns unknown/unsupported) |

## Blockers

- Unreal Engine installation path is environment-specific and not hardcoded.
- Full Blueprint graph authoring coverage is intentionally limited to validated node types.
- Live acceptance criteria requiring Editor interaction remain open until a UE project is available for smoke testing.
