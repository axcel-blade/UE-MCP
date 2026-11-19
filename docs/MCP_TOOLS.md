# MCP Tools

Tools are registered in Python under mcp_server/tools/*/tools.py and executed by the C++ plugin when a handler exists.

Categories: system, actors, levels, blueprints, assets, materials, lighting, meshes, animation, niagara, widgets, sequencer, rendering, physics, gameplay, project, testing, intelligence, workflows, pipeline.

For live availability inside a running Editor, call unreal_list_tools.

Unsupported handlers return:

`json
{"success": false, "error": {"code": "unsupported", "message": "..."}}
`

See docs/IMPLEMENTATION_STATUS.md for phase coverage.
