# Games

Tools: `unreal_create_game_mode`, `unreal_set_world_game_mode`, `unreal_add_player_start`, `unreal_add_nav_mesh_volume`, `unreal_create_input_action` (Enhanced Input action + mapping context), `unreal_add_trigger_volume`, `unreal_play_in_editor` / `unreal_stop_play`, plus Blueprint tools (`unreal_create_blueprint`, variables, nodes, compile).

Workflow: block out the level (`unreal_create_room`, `unreal_build_scene`) -> game mode + pawn -> player start -> navigation volume -> input actions -> gameplay Blueprints -> PIE test (`unreal_play_in_editor`, check `unreal_get_output_log`) -> `unreal_save_all`.
