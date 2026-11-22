# Implementation Status

Last updated: 2026-11-22  
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
| Project / testing | Implemented (diagnostics/save/console/editor Python; build unsupported) |
| Intelligence | Implemented (bounded analyzers) |
| Physics | Partial (simulate/collision/mass/gravity) |
| Animation / Niagara / UMG / Sequencer / Meshes | Stubbed as `unsupported` until implemented |
| Gameplay domain C++ | Not yet registered (Python forwards; plugin returns unknown/unsupported) |

## Editor Python and industry packs (live-verified on UE 5.8.4)

`unreal_execute_editor_python` runs through PythonScriptPlugin from the core ticker
(safe for imports and map loads). The server builds on it:

| Area | Tools | Live result |
|---|---|---|
| Scripting | `unreal_execute_python`, `unreal_lookup_api`, `unreal_get_guide`, `unreal_search_scene`, `unreal_look`, `unreal_open_editor`, `unreal_close_editor` | Passed |
| Online assets | `unreal_search_online_assets`, `unreal_import_online_asset` | Poly Haven model + HDRI passed; Poly Pizza / Sketchfab need keys (not exercised) |
| Games | `unreal_create_game_mode`, `unreal_set_world_game_mode`, `unreal_add_player_start`, `unreal_add_nav_mesh_volume`, `unreal_add_trigger_volume`, `unreal_create_input_action`, `unreal_play_in_editor`, `unreal_stop_play` | Passed |
| Film / video | `unreal_create_cinematic`, `unreal_add_transform_keys`, `unreal_set_cine_camera`, `unreal_list_level_sequences`, `unreal_render_sequence_mrq`, `unreal_get_render_status` | Passed (96- and 180-frame MRQ renders) |
| Live events / VP | `unreal_get_virtual_production_status`, `unreal_list_livelink_subjects`, `unreal_create_led_stage`, `unreal_create_display_wall`, `unreal_create_lighting_cue` | Passed (no live Live Link source connected) |
| Automotive / product | `unreal_import_cad`, `unreal_create_product_studio`, `unreal_create_turntable`, `unreal_create_variant_set`, `unreal_activate_variant`, `unreal_measure` | Passed (OBJ path; Datasmith CAD formats not exercised without sample files) |
| Simulation | `unreal_spawn_from_data`, `unreal_create_conveyor`, `unreal_create_physics_stack`, `unreal_run_simulation` | Passed |

Pack tools run vetted templates, so they work without `allow_python_execution`.
Failed pack calls destroy the actors they spawned; asset creation is not undoable,
so templates validate inputs before creating assets.

## Blockers

- Unreal Engine installation path is environment-specific and not hardcoded.
- Full Blueprint graph authoring coverage is intentionally limited to validated node types.
- Live acceptance criteria requiring Editor interaction remain open until a UE project is available for smoke testing.
