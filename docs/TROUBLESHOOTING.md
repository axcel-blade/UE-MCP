# Troubleshooting

## Connection refused

- Is the Editor running **with a project open**? The bridge only starts when the UnrealEngineMCP project plugin loads.
- Is Unreal Engine MCP enabled?
- Check port `55557` is free and matches config (`UNREAL_ENGINE_MCP_PORT`).
- Look for bridge bind errors in Output Log.
- Run `uv run python scripts/test_connection.py` and `uv run python scripts/diagnose.py`.

## Plugin “designed for build 5.x” / incompatible dialog

The Editor plugin ships as **source** and is meant for UE **5.3+** (verified on **5.8**). The `.uplugin` intentionally omits `EngineVersion` so newer Editors (5.4–5.8, …) do not block on a version mismatch dialog. Rebuild the plugin for each Editor version.

If you still see the dialog (older plugin install):

1. Update/reinstall the plugin from this repo (`uv run python scripts/install_plugin.py --project …`).
2. Or click **Yes** once to load anyway, then rebuild so `Binaries/` matches your Editor.

## Bridge never listens after opening the project

- Confirm Output Log contains `UnrealEngineMCP bridge listening on 127.0.0.1:55557`.
- Ensure `Plugins/UnrealEngineMCP/Binaries/` contains `UnrealEditor-UnrealEngineMCP.dll` built for your engine.
- Close Live Coding / the Editor before a clean rebuild if the module lock blocks compilation.

## Plugin not compiling

- Enable **Editor Scripting Utilities**.
- Confirm Visual Studio 2022 C++ workload (or Rider).
- Delete `Intermediate/` / `Binaries/` under the plugin and rebuild.
- Ensure the plugin lives at `<Project>/Plugins/UnrealEngineMCP/`.

## One-liner install fails (Windows)

- PowerShell scripts must be **UTF-8 without BOM**. Prefer the published Pages URL, not a re-saved copy with a BOM.
- Require Git + network access to GitHub and `astral.sh` (for uv).
- Override install location with `UE_MCP_HOME`; branch with `UE_MCP_BRANCH`.

## Pages / install site 404

- Enable **Settings → Pages → Source: GitHub Actions**.
- Ensure `site/` is on `main` and the **Pages** deploy job succeeded (builds also run on `develop`).
- Website URL: [https://axcel-blade.github.io/UE-MCP/](https://axcel-blade.github.io/UE-MCP/)

## Tools return unsupported

Expected for creative-domain tools not yet implemented in C++. Check [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## Safe mode permission denied

Switch `security.mode` / `UNREAL_ENGINE_MCP_SECURITY_MODE` to `advanced`, or use an allowed tool. Destructive tools need `confirmed=true`.
