# Unreal editor Python (unreal_execute_python)

- `unreal` is preloaded. Set `result = ...` (or end with an expression) to return data; return dicts/lists of plain values.
- Prefer editor subsystems over deprecated libraries:
  - actors: `unreal.get_editor_subsystem(unreal.EditorActorSubsystem)` (`get_all_level_actors`, `spawn_actor_from_class`, `spawn_actor_from_object`, `destroy_actor`)
  - levels: `unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)` (`new_level`, `load_level`, `save_current_level`, `editor_play_simulate`, `editor_request_end_play`)
  - assets: `unreal.EditorAssetLibrary`, `unreal.AssetToolsHelpers.get_asset_tools()`, `unreal.AssetRegistryHelpers.get_asset_registry()`
  - viewport: `unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)` (`get/set_level_viewport_camera_info`)
- Units are centimeters, Z-up, rotators are (pitch, yaw, roll) in degrees: `unreal.Rotator(roll=, pitch=, yaw=)` takes keyword args.
- Properties: `obj.get_editor_property("name")` / `obj.set_editor_property("name", value)`. Look names up with `unreal_lookup_api`.
- Wrap edits in `with unreal.ScopedEditorTransaction("label"):` so the user can undo them.
- Long work: pass `timeout` (seconds). Never call `quit_editor`, console commands or delete APIs here; the safety check refuses them, use the dedicated tools.
- Asset paths look like `/Game/Folder/Asset` (package) or `/Game/Folder/Asset.Asset` (object).
