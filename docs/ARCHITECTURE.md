# Architecture

## Overview

UnrealEngineMCP connects MCP clients to a running Unreal Editor through three layers:

1. **Python MCP server** (`mcp_server/`) — FastMCP over STDIO, validation, security, orchestration
2. **Communication bridge** — length-prefixed JSON over localhost TCP (default `127.0.0.1:55557`)
3. **C++ Editor plugin** (`UnrealEngineMCP/`) — Tool registry + GameThread dispatcher + Unreal Editor APIs

## Design principles

- C++ owns engine mutations; Python owns MCP protocol and multi-step workflows.
- Network I/O never touches UObjects directly.
- Safe mode is default; destructive and script tools are gated.
- Unsupported capabilities return structured errors, never fake success.
- Version-aware plugin targeting UE 5.x with EditorScriptingUtilities.

## Request path

1. MCP client invokes a tool.
2. Python validates permissions and arguments.
3. `TcpClient` sends `{id, version, method, params, auth?}` framed with a 4-byte length.
4. Plugin network thread reads the frame and dispatches to `FUnrealEngineMCPRequestDispatcher`.
5. Handler runs on the Game Thread and returns `{id, ok, result|error, duration_ms}`.

## Related references

- Blender-MCP: STDIO MCP + TCP addon + main-thread queue
- flopperam Unreal MCP: C++ TCP bridge patterns
- IvanMurzak Unreal-MCP: GameThread dispatcher patterns (not adopting .NET sidecar)
