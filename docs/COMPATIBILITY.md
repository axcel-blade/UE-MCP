# Compatibility

| Component | Support |
|---|---|
| Unreal Engine | 5.3+ target (source plugin; rebuild per Editor); verified on **UE 5.8**; `.uplugin` omits `EngineVersion` to avoid mismatch dialogs on 5.4+ |
| Platforms | Windows primary; plugin descriptors allow Mac/Linux |
| MCP clients | Any STDIO MCP client |
| Python | 3.11+ |

### UE 5.8 notes

- Rebuild the Editor plugin against UE 5.8 binaries (`RunUAT BuildPlugin` or project compile).
- Do not call `FEditorFileUtils::LoadMap` directly inside `AsyncTask(GameThread, …)` — UE 5.8 asserts in `EditorServer.cpp`. `unreal_open_level` schedules the load on the next `FTSTicker` tick instead.
- Prefer `TAtomic`/`++`/`Load(EMemoryOrder::…)` over older `FThreadSafeCounter` patterns when touching the TCP bridge.

Version-specific API differences should be isolated behind compatibility helpers as they are discovered.
