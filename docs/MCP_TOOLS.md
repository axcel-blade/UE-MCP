# MCP Tools

Tools are registered in Python under mcp_server/tools/*/tools.py and executed by the C++ plugin when a handler exists.

Categories: system, actors, levels, blueprints, assets, materials, lighting, meshes, animation, niagara, widgets, sequencer, rendering, physics, gameplay, project, testing, intelligence, workflows, pipeline, scripting, industries, online_assets, production.

For live availability inside a running Editor, call unreal_list_tools.

Unsupported handlers return:

`json
{"success": false, "error": {"code": "unsupported", "message": "..."}}
`

See docs/IMPLEMENTATION_STATUS.md for phase coverage.

## Production pack (`mcp_server/tools/production`)

Vetted editor-Python templates (one undo step; spawned actors are destroyed if a call
fails) plus server-side project-file tools. Every tool checks the permission gates.
Results are verified in the editor before success is reported.

| Tool | What it does | Gate |
|---|---|---|
| `unreal_spawn_actor_pattern` | grid / line / circle / random_region (min distance) / path placement, seeded | advanced |
| `unreal_build_structure` | wall, fence, floor, staircase, room (door gap), multi-floor building, tower | advanced |
| `unreal_organize_actors` | move actors into outliner folders | advanced |
| `unreal_list_levels` | World assets under a path + current level | safe |
| `unreal_duplicate_level` | duplicate a level (never overwrites) | advanced |
| `unreal_delete_level` | delete a level (refuses the open one) | destructive, `confirmed=true` |
| `unreal_create_pcg_volume` / `unreal_generate_pcg` | PCGVolume with graph + seed, generate / cleanup | PCG plugin |
| `unreal_create_terrain_mesh` | fractal-noise heightfield DynamicMesh with collision | Geometry Script plugin |
| `unreal_create_ai_assets` | Blackboard (typed keys) + Behavior Tree + AIController BP | advanced |
| `unreal_create_sound_cue` / `unreal_create_sound_attenuation` / `unreal_spawn_ambient_sound` | audio assets and placement | advanced |
| `unreal_place_niagara_effect` | NiagaraActor for an existing system + user parameters | Niagara |
| `unreal_list_project_plugins` / `unreal_set_plugin_enabled` | read / edit `.uproject` plugins (writes `.uproject.bak`) | set: `confirmed=true` |
| `unreal_create_cpp_class` | UCLASS scaffolding for 16 class kinds in the project module; never overwrites | advanced |
| `unreal_get_output_log` | tail/filter `Saved/Logs/<Project>.log` | safe |
| `unreal_build_project` | UnrealBuildTool build with parsed errors/warnings | restricted, `confirmed=true` |
