# Getting Started

1. Install via the [one-liner](INSTALLATION.md) or clone and `uv sync`.
2. Install the plugin into your Unreal project:

```powershell
uv run python scripts/install_plugin.py --project "D:\Path\To\YourProject.uproject"
```

3. Open Unreal Editor with **UnrealEngineMCP** (+ Editor Scripting Utilities) enabled; compile if prompted.
4. Confirm Output Log shows UnrealEngineMCP bridge listening on `127.0.0.1:55557`.
5. Start your MCP client with the `unreal-engine-mcp` config (`uv run ...`).
6. Call `unreal_ping`.
7. Call `unreal_get_all_actors`.
8. Spawn a cube with `unreal_spawn_actor`.
9. Capture with `unreal_capture_viewport`.

Recommended first workflow prompt: `unreal_scene_builder`.

Install site: [https://axcel-blade.github.io/UE-MCP/](https://axcel-blade.github.io/UE-MCP/)
