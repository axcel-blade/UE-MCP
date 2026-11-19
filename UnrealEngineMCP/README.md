# UnrealEngineMCP Editor Plugin

C++ Unreal Engine 5 Editor plugin that hosts the localhost TCP bridge and executes MCP tool methods on the Game Thread.

## Defaults

- Host: `127.0.0.1`
- Port: `55557`
- Protocol: length-prefixed JSON v1.0

## Settings

**Edit → Project Settings → Plugins → Unreal MCP**

- Bind address / port
- Auto-start
- Auth token
- Screenshot directory

## Modules

- `Bridge/` TCP server, framing, dispatch
- `Core/` registry, GameThread dispatcher, serializers
- `Tools/` domain handlers

## Build

Copy into `<Project>/Plugins/UnrealEngineMCP`, regenerate project files, compile Editor target. Requires **Editor Scripting Utilities**.

From the repo root (preferred):

```powershell
uv run python scripts/install_plugin.py --project "D:\Path\To\YourProject.uproject"
```

Project docs / one-liner install: [https://axcel-blade.github.io/UE-MCP/](https://axcel-blade.github.io/UE-MCP/) · [docs/INSTALLATION.md](../docs/INSTALLATION.md)
