# Compatibility

| Component | Support |
|---|---|
| Unreal Engine | 5.3+ target (source plugin; rebuild per Editor); `.uplugin` omits `EngineVersion` to avoid mismatch dialogs on 5.4+ |
| Platforms | Windows primary; plugin descriptors allow Mac/Linux |
| MCP clients | Any STDIO MCP client |
| Python | 3.11+ |

Version-specific API differences should be isolated behind compatibility helpers as they are discovered.
