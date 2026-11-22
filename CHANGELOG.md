# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Editor Python execution through PythonScriptPlugin (`unreal_execute_python`, alias `unreal_execute_editor_python`) with Blender-MCP-style restricted / confirmation / trusted modes and a static AST safety check (no subprocess, file or asset deletion, network, quit, console commands or eval)
- `unreal_look` returns viewport screenshots as MCP images (lit, unlit, wireframe, detail lighting, lighting only, multi-angle); `unreal_capture_viewport` gains `max_size` (inline base64 PNG) and `view_mode`
- `unreal_lookup_api`, `unreal_get_guide` (unreal_python, games, film, live_events, automotive, simulation), `unreal_search_scene`, `unreal_open_editor`, `unreal_close_editor`
- Online assets from Poly Haven, Poly Pizza and Sketchfab: `unreal_search_online_assets`, `unreal_import_online_asset` (models, texture sets, HDRI sky light)
- Industry packs: games (game mode, player start, nav mesh, triggers, Enhanced Input, PIE), film (cinematics, transform keys, CineCamera lens, Movie Render Queue), live events / virtual production (LED stage, display wall, lighting cues, Live Link / nDisplay status), automotive / product (CAD import incl. Datasmith, product studio, turntable, Variant Manager configurator, measure), simulation (digital-twin spawn, conveyor, physics stack, timed Simulate-in-Editor)
- Config: `security.script_permission`, `security.safe_python_execution`, `editor.*`, `providers.*`; env `UNREAL_ENGINE_MCP_ALLOW_PYTHON`, `UNREAL_ENGINE_MCP_SCRIPT_PERMISSION`, `UNREAL_ENGINE_MCP_EDITOR`, `UNREAL_ENGINE_MCP_PROJECT`, `SKETCHFAB_API_TOKEN`

### Changed

- `unreal_create_game_mode`, `unreal_create_input_action`, `unreal_create_cinematic`, `unreal_create_lighting_cue` and `unreal_create_turntable` take `overwrite` to replace an existing asset instead of failing
- `unreal_create_conveyor` takes `friction` (bed physical material, default 0.1) and reports `low_end_z`, `horizontal_run` and `parts_slide`
- `unreal_run_simulation` waits for simulated time, reports `simulated_seconds`, and disables background CPU throttling for the run (new bridge command `unreal_set_play_throttle_override`)

### Fixed

- `unreal_add_blueprint_variable` with `float`/`double` crashed the editor (UE5 `PC_Real` pin without float/double subcategory); unknown types and duplicate names now return errors
- `unreal_save_all` hung the bridge on a modal "Save As" dialog for untitled maps; untitled packages are now skipped and reported in `skipped_untitled`
- `unreal_spawn_actor` / `unreal_create_blueprint` silently fell back to `StaticMeshActor` / `Actor` for unknown classes; they now fail with an error
- `unreal_add_blueprint_function` created an unnamed graph when `function_name` was missing, and allowed duplicates
- `unreal_rename_asset` now validates input and accepts `destination_path` as well as `new_name`
- Workflow tools (`unreal_create_room`, `unreal_setup_lighting`, `unreal_setup_camera`, `unreal_build_scene`, `unreal_create_gameplay_prototype`) rejected their documented arguments because `**params` became a required `params` field; `params` is now optional and still overrides
- `unreal_setup_camera` sent the wrong payload to `unreal_set_viewport_location` and never applied the rotation
- `unreal_spawn_actor` crashed the editor (fatal "Cannot generate unique name") when the requested name was already in use, including by a just-deleted actor; the name is now a request and the label stays exact
- `unreal_create_blueprint_node` with `BeginPlay` added a duplicate event to Blueprints that already had one, breaking compilation; it now reuses the existing node (`existing: true`)
- `unreal_compile_blueprint` failures now include the compiler error messages, which are also returned by `unreal_get_compile_errors`
- `unreal_set_material_parameter` silently set vector parameters to white unless the colour was nested as `value: {r,g,b}`, and reported success for parameters that don't exist; it now accepts top-level `r/g/b/a`, `value` as an object or array, validates the parameter name and value, echoes the applied value, and refreshes the instance
- Asset import and editor Python could crash the editor (TaskGraph `RecursionGuard` assertion) because they ran inside a task-graph game-thread task; they now run from the core ticker
- `unreal_capture_viewport` failed with "No active viewport" after a level load; it now falls back to the level viewport
- `unreal_set_material_parameter` infers `vector` when colour values are given without `type`
- `unreal_run_simulation` advanced physics only ~1/10 of the requested time when the editor was in the background (throttled to ~3 FPS with physics clamped per frame)
- `unreal_create_conveyor` mixed belt length and horizontal run on slopes, placing parts past the bed and the low end underground; the low end is now validated to stay above ground
- Re-running `unreal_create_variant_set` added duplicate sets ("Paint0"); a set with the same name is now replaced
- Overwriting an input action left a stale null mapping in the reused mapping context; stale and duplicate mappings are now removed
- `unreal_create_led_stage` and `unreal_create_display_wall` now group their actors in an Outliner folder named after `label`
- `unreal_capture_viewport` could report success without ever writing a file when the editor was backgrounded; it now forces a viewport draw and returns `file_written`

## [1.0.4] - 2026-11-20

### Fixed

- TCP client reconnects once after a mid-request bridge drop and surfaces clearer “Editor still open?” guidance when connection is refused or lost
- `unreal_save_level` no longer opens a modal save/checkout dialog that blocked the game thread and hung the bridge; untitled maps now return a clear error
- `unreal_create_level` saves the new map to disk so `unreal_open_level` can find it (previously work continued in the old map)
- Screenshot tools resolve the relative default `ScreenshotDirectory` against the project instead of `Engine/Binaries/Win64`, and append `.png` when missing

## [1.0.3] - 2026-11-19

### Fixed

- `unreal_open_level` defers `FEditorFileUtils::LoadMap` to the next core tick so UE 5.8 no longer fatals when opening a level from the MCP game-thread dispatcher
- Dispatcher flattens nested `{"params": {...}}` tool arguments so Cursor MCP hosts apply spawn/location/name fields correctly
- Document UE 5.8 verification notes in compatibility / troubleshooting docs

## [1.0.2] - 2026-11-19

### Fixed

- Omit `EngineVersion` from `UnrealEngineMCP.uplugin` so UE 5.4+ no longer blocks on the “designed for build 5.3.0” incompatible-plugin dialog (source plugin still targets 5.3+)
- TCP bridge now accepts concurrent MCP clients on worker threads and uses blocking reads so persistent connections no longer drop between requests (`0 bytes read` / rapid connect-disconnect)
- Document project-must-be-open and incompatible-dialog troubleshooting for the Editor bridge

## [1.0.1] - 2026-11-19

### Fixed

- Asset reimport (`reimport_asset` / related tools) now uses `FReimportManager` instead of `UEditorAssetLibrary::ReimportAsset` for reliable Editor reimports

## [1.0.0] - 2026-11-19

### Added

- Unreal Engine MCP 1.0.0: Python FastMCP server (uv), length-prefixed TCP bridge, C++ Unreal Editor plugin
- Core tool families: system, actors, levels, assets, blueprints, materials, lighting, rendering, project, intelligence, physics
- Safe / advanced security modes and localhost-default bridge
- Astro GitHub Pages install site with UTF-8 remote installers and local `installers/`
- CI, CD, Pages, and Release GitHub Actions workflows
- Branch protection on `main` and `develop`
- Installation scripts, docs, and pytest suite

### Changed

- Docs aligned with Pages one-liners, Git Flow, and website https://axcel-blade.github.io/UE-MCP/
