# Configuration

Primary file: `config/config.json`

## Environment overrides

| Variable | Effect |
|---|---|
| `UNREAL_ENGINE_MCP_CONFIG` | Path to config JSON |
| `UNREAL_ENGINE_MCP_HOST` | Bridge host |
| `UNREAL_ENGINE_MCP_PORT` | Bridge port |
| `UNREAL_ENGINE_MCP_AUTH_TOKEN` | Shared auth token |
| `UNREAL_ENGINE_MCP_SECURITY_MODE` | `safe` or `advanced` |
| `UNREAL_ENGINE_MCP_LOG_LEVEL` | Logging level |
| `UE_MCP_HOME` | Remote installer clone directory (default `~/UE-MCP`) |
| `UE_MCP_BRANCH` | Remote installer git branch (default `main`) |

Plugin settings are also available under **Edit → Project Settings → Plugins → Unreal MCP**.

## Launching with uv

Prefer MCP client configs that use:

```text
uv run --directory <repo> unreal-engine-mcp
```

See `config/mcp_clients/`.
