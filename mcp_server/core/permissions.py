"""Security mode gates for tool execution."""

from __future__ import annotations

from mcp_server.config import Settings
from mcp_server.exceptions import PermissionError_

SAFE_ALLOWED_PREFIXES = (
    "unreal_ping",
    "unreal_get_",
    "unreal_list_",
    "unreal_find_",
    "unreal_search_",
    "unreal_capture_",
    "unreal_analyze_",
    "unreal_validate_",
)

SAFE_ALLOWED_EXACT = {
    "unreal_spawn_actor",
    "unreal_set_actor_transform",
    "unreal_set_actor_location",
    "unreal_set_actor_rotation",
    "unreal_set_actor_scale",
    "unreal_rename_actor",
    "unreal_set_actor_visibility",
    "unreal_duplicate_actor",
    "unreal_attach_actor",
    "unreal_detach_actor",
    "unreal_add_component",
    "unreal_save_level",
    "unreal_open_level",
    "unreal_create_level",
    "unreal_save_asset",
    "unreal_save_all",
    "unreal_import_asset",
    "unreal_create_folder",
    "unreal_create_material",
    "unreal_create_material_instance",
    "unreal_assign_material",
    "unreal_set_material_parameter",
    "unreal_compile_material",
    "unreal_save_material",
    "unreal_create_directional_light",
    "unreal_create_point_light",
    "unreal_create_spot_light",
    "unreal_create_rect_light",
    "unreal_create_sky_light",
    "unreal_create_sky_atmosphere",
    "unreal_create_exponential_height_fog",
    "unreal_set_light_intensity",
    "unreal_set_light_color",
    "unreal_set_light_temperature",
    "unreal_set_viewport_camera",
    "unreal_set_viewport_location",
    "unreal_set_viewport_rotation",
    "unreal_create_blueprint",
    "unreal_compile_blueprint",
    "unreal_save_blueprint",
    "unreal_add_blueprint_variable",
    "unreal_add_blueprint_function",
    "unreal_add_blueprint_event",
    "unreal_create_blueprint_node",
    "unreal_connect_blueprint_nodes",
    "unreal_add_blueprint_component",
    "unreal_create_room",
    "unreal_build_scene",
    "unreal_setup_lighting",
    "unreal_setup_camera",
    "unreal_create_gameplay_prototype",
    "unreal_optimize_scene",
    "unreal_validate_project",
    "unreal_job_status",
    "unreal_import_blender_fbx",
    "unreal_validate_blender_import",
    "unreal_engine_mcp_version",
}

DESTRUCTIVE_TOOLS = {
    "unreal_delete_actor",
    "unreal_delete_asset",
    "unreal_delete_blueprint",
    "unreal_delete_material_expression",
    "unreal_delete_blueprint_node",
    "unreal_remove_component",
    "unreal_remove_blueprint_variable",
    "unreal_remove_widget",
    "unreal_delete_level",
    "unreal_set_plugin_enabled",
}

RESTRICTED_TOOLS = {
    "unreal_execute_editor_python",
    "unreal_execute_console_command",
    "unreal_run_build",
    "unreal_build_project",
}


def assert_tool_allowed(settings: Settings, tool_name: str, *, confirmed: bool = False) -> None:
    mode = settings.security.mode
    if tool_name in RESTRICTED_TOOLS:
        if mode != "advanced":
            raise PermissionError_(f"Tool '{tool_name}' requires advanced security mode")
        if (
            tool_name == "unreal_execute_editor_python"
            and not settings.security.allow_python_execution
        ):
            raise PermissionError_("Python execution is disabled in configuration")
        if (
            tool_name == "unreal_execute_console_command"
            and not settings.security.allow_console_commands
        ):
            raise PermissionError_("Console commands are disabled in configuration")

    if (
        tool_name in DESTRUCTIVE_TOOLS
        and settings.security.require_confirmation_for_destructive_actions
        and not confirmed
    ):
        raise PermissionError_(
            f"Tool '{tool_name}' is destructive. Pass confirmed=true to proceed."
        )

    if mode == "safe":
        allowed = (
            tool_name in SAFE_ALLOWED_EXACT
            or tool_name in DESTRUCTIVE_TOOLS
            or any(tool_name.startswith(p) for p in SAFE_ALLOWED_PREFIXES)
        )
        if not allowed:
            raise PermissionError_(
                f"Tool '{tool_name}' is not permitted in safe mode. Switch to advanced mode."
            )
