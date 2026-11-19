# Engineering Decision Log

## D001 — Architecture: Blender-MCP style bridge over .NET sidecar

**Date:** 2026-11-19  
**Decision:** Use a Python FastMCP STDIO server plus a C++ Unreal Editor plugin that exposes a localhost TCP bridge.  
**Context:** IvanMurzak/Unreal-MCP uses a .NET sidecar and SignalR-oriented hosting. Flopperam uses a C++ TCP bridge with a Python MCP server. Blender-MCP (axcel-blade) uses Python STDIO MCP → TCP → in-app addon.  
**Rationale:** Matches the project requirement for Python MCP + C++ plugin without embedding the MCP server inside Unreal. Keeps C++ as the execution layer and Python as orchestration. Avoids a .NET runtime dependency on Windows editor setups.  
**Consequences:** Protocol and tool surface are owned by this repo. Cannot reuse IvanMurzak extension packaging as-is.

## D002 — Framing: length-prefixed JSON

**Date:** 2026-11-19  
**Decision:** Use 4-byte big-endian length prefix + UTF-8 JSON body.  
**Context:** Blender-MCP uses NDJSON. Flopperam uses raw JSON without a robust length frame.  
**Rationale:** Unambiguous message boundaries for large Blueprint/asset payloads and screenshot metadata.  
**Consequences:** Clients must speak protocol v1; NDJSON clients are incompatible.

## D003 — Threading model

**Date:** 2026-11-19  
**Decision:** Accept TCP on an `FRunnable` network thread; execute all UObject/Editor work via `AsyncTask(ENamedThreads::GameThread)` with promise/future wait.  
**Rationale:** Unreal Editor APIs are not network-thread safe.  
**Consequences:** Long GameThread work can stall the editor; long jobs should return async job IDs in later phases.

## D004 — Security default: Safe Mode

**Date:** 2026-11-19  
**Decision:** Default `security.mode = safe`; bind `127.0.0.1`; optional shared auth token; destructive tools require `confirmed=true`; Python/console execution advanced-only.  
**Rationale:** Local AI agents can still do damage; least privilege by default.

## D005 — Tool registration strategy

**Date:** 2026-11-19  
**Decision:** Python registers MCP tools that forward to the plugin by method name. C++ `FUnrealEngineMCPToolRegistry` owns real handlers. High-level workflows compose lower-level calls in Python.  
**Rationale:** Single source of engine truth in C++; Python stays thin except for multi-step orchestration.

## D006 — Phase honesty over feature theater

**Date:** 2026-11-19  
**Decision:** Unsupported creative-domain tools return structured `unsupported` errors rather than simulated success.  
**Rationale:** Spec forbids fake success responses. Documentation and `IMPLEMENTATION_STATUS.md` track real coverage.

## D007 — Python toolchain: uv

**Date:** 2026-11-19  
**Decision:** Use `uv` for Python environment sync, locking (`uv.lock`), tests, and MCP client launch (`uv run unreal-engine-mcp`).  
**Rationale:** Fast, reproducible installs; matches modern MCP packaging practice (including Blender-MCP). Avoids manual venv/pip workflows.

## D008 — Git Flow + GitHub community files

**Date:** 2026-11-19  
**Decision:** Adopt Git Flow (`main`, `develop`, `feature/*`, `release/*`, `hotfix/*`) with uppercase root community markdown (`CONTRIBUTING`, `SECURITY`, `SUPPORT`, `CHANGELOG`, `CODE_OF_CONDUCT`) and Actions workflows for CI, CD, and Release.  
**Rationale:** Clear contribution path, reproducible releases via tags `v*`, and GitHub-native security/support surfaces.

## D009 — Astro Pages install site + UTF-8 installers

**Date:** 2026-11-19  
**Decision:** Ship an Astro + pnpm site under `site/` on GitHub Pages (`/UE-MCP`), with remote `install.ps1` / `install.sh` (UTF-8 no BOM) and local `installers/*`, mirroring Blender-MCP. Protect `main` / `develop` with PR + review rules.  
**Rationale:** One-liner onboarding, consistent maintainer UX across axcel-blade MCP repos, and safer default branches.  
**Consequences:** Pages workflow must stay green when `site/**` changes; PowerShell installers must never gain a UTF-8 BOM.

## D010 — Repository website / About metadata

**Date:** 2026-11-19  
**Decision:** Set GitHub repository homepage to `https://axcel-blade.github.io/UE-MCP/` and enable Pages via GitHub Actions.  
**Rationale:** Same discoverability pattern as Blender-MCP (About → Website).
