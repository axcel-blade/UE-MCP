# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Astro GitHub Pages install site (`site/`) with UTF-8 remote installers (`install.ps1` / `install.sh`)
- Local OS installers under `installers/windows|macos|linux`
- Pages workflow (`.github/workflows/pages.yml`) and CD job to refresh Pages on release
- Repository website link: https://axcel-blade.github.io/UE-MCP/
- Branch protection on `main` and `develop` (PR + review + conversation resolution)

### Changed

- Installation / Getting Started / Development docs aligned with Pages one-liners and Git Flow protection

### Fixed

-

## [0.1.0] - 2026-11-19

### Added

- Initial UnrealEngineMCP foundation: Python FastMCP server (uv), length-prefixed TCP bridge, C++ Unreal Editor plugin
- Core tool families: system, actors, levels, assets, blueprints, materials, lighting, rendering, project, intelligence, physics
- Safe / advanced security modes and localhost-default bridge
- Installation scripts, docs, pytest suite, and GitHub CI/CD/release workflows
