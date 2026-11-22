# Live events, broadcast and virtual production

Tools: `unreal_create_led_stage` (curved LED volume + floor + tracked CineCamera for ICVFX blocking), `unreal_get_virtual_production_status` (nDisplay / Live Link / DMX / OCIO plugin availability and nDisplay configs in the project), `unreal_list_livelink_subjects`, `unreal_create_lighting_cue` (sequence that animates light intensity/colour for show control), `unreal_create_display_wall` (media/screen planes).

nDisplay cluster configs are authored as nDisplay Config assets; this MCP reports and spawns them but cluster launch happens outside the editor (Switchboard).
