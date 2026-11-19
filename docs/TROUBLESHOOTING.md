# Troubleshooting

## Connection refused

- Is the Editor running?
- Is Unreal Engine MCP enabled?
- Check port `55557` is free and matches config (`UNREAL_ENGINE_MCP_PORT`).
- Look for bridge bind errors in Output Log.
- Run `uv run python scripts/test_connection.py` and `uv run python scripts/diagnose.py`.

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
