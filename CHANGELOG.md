# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

-

### Changed

-

### Fixed

- `unreal_add_blueprint_variable` with `float`/`double` crashed the editor (UE5 `PC_Real` pin without float/double subcategory); unknown types and duplicate names now return errors
- `unreal_save_all` hung the bridge on a modal "Save As" dialog for untitled maps; untitled packages are now skipped and reported in `skipped_untitled`
- `unreal_spawn_actor` / `unreal_create_blueprint` silently fell back to `StaticMeshActor` / `Actor` for unknown classes; they now fail with an error
- `unreal_add_blueprint_function` created an unnamed graph when `function_name` was missing, and allowed duplicates
- `unreal_rename_asset` now validates input and accepts `destination_path` as well as `new_name`
- Workflow tools (`unreal_create_room`, `unreal_setup_lighting`, `unreal_setup_camera`, `unreal_build_scene`, `unreal_create_gameplay_prototype`) rejected their documented arguments because `**params` became a required `params` field; `params` is now optional and still overrides
- `unreal_setup_camera` sent the wrong payload to `unreal_set_viewport_location` and never applied the rotation
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
