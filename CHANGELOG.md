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

-

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
