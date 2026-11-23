"""Production pack: templates are valid Python, gates apply, file tools are safe."""

from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp.server.fastmcp import FastMCP
from mcp_server.config import Settings
from mcp_server.core import python_exec
from mcp_server.tools.production import cpp_templates
from mcp_server.tools.production import tools as production


class _Resp:
    def __init__(self, result) -> None:
        self.ok, self.result, self.error, self.duration_ms = True, result, None, 1.0


class _Client:
    """Captures editor code; answers project-path queries with ``paths``."""

    def __init__(self, paths: dict | None = None) -> None:
        self.codes: list[str] = []
        self.paths = paths or {}

    async def request(self, method, params, **kw):
        code = params["code"]
        self.codes.append(code)
        payload = self.paths if "get_project_file_path" in code else {"ok": 1}
        line = python_exec.MARKER + json.dumps({"ok": True, "result": payload, "stdout": ""})
        return _Resp({"log": [{"type": "Info", "output": line}]})


def _setup(paths: dict | None = None, **security):
    client = _Client(paths)
    ctx = SimpleNamespace(
        settings=Settings.model_validate({"security": security or {"mode": "advanced"}}),
        dispatcher=SimpleNamespace(client=client),
    )
    mcp = FastMCP("t")
    production.register(mcp, ctx)
    return mcp, client


def _call(mcp, _tool, **kw) -> dict:
    res = asyncio.run(mcp.call_tool(_tool, kw))
    content = res[0] if isinstance(res, tuple) else res
    return json.loads(content[0].text)


TEMPLATE_CALLS = {
    "unreal_spawn_actor_pattern": {"pattern": "grid"},
    "unreal_build_structure": {"kind": "room", "name": "Hut"},
    "unreal_organize_actors": {"folder": "X", "label_contains": "Hut"},
    "unreal_list_levels": {},
    "unreal_duplicate_level": {"source": "/Game/A", "destination": "/Game/B"},
    "unreal_delete_level": {"level": "/Game/A", "confirmed": True},
    "unreal_create_pcg_volume": {"label": "PCG", "graph": "/Game/G"},
    "unreal_generate_pcg": {"label": "PCG"},
    "unreal_create_terrain_mesh": {},
    "unreal_create_ai_assets": {},
    "unreal_create_sound_cue": {"path": "/Game/S", "sound_wave": "/Game/W"},
    "unreal_create_sound_attenuation": {"path": "/Game/A"},
    "unreal_spawn_ambient_sound": {"sound": "/Game/S"},
    "unreal_place_niagara_effect": {"system": "/Game/N"},
}


@pytest.mark.parametrize(("tool", "args"), TEMPLATE_CALLS.items())
def test_templates_are_valid_python(tool: str, args: dict) -> None:
    mcp, client = _setup()
    out = _call(mcp, tool, **args)
    assert out["success"], out
    ast.parse(client.codes[-1])


def test_all_tools_registered() -> None:
    mcp, _ = _setup()
    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert set(TEMPLATE_CALLS) <= names
    assert {
        "unreal_create_cpp_class",
        "unreal_build_project",
        "unreal_get_output_log",
        "unreal_set_plugin_enabled",
        "unreal_list_project_plugins",
    } <= names


def test_destructive_and_restricted_gates() -> None:
    mcp, client = _setup()
    out = _call(mcp, "unreal_delete_level", level="/Game/A")
    assert not out["success"] and "confirmed" in out["error"]["message"]
    assert client.codes == []
    mcp, _ = _setup(mode="safe")
    assert not _call(mcp, "unreal_build_project", confirmed=True)["success"]
    assert not _call(mcp, "unreal_spawn_actor_pattern", pattern="grid")["success"]


def test_pattern_count_validated() -> None:
    mcp, client = _setup()
    assert not _call(mcp, "unreal_spawn_actor_pattern", pattern="grid", count=0)["success"]
    assert client.codes == []


@pytest.mark.parametrize("kind", list(cpp_templates.CLASS_KINDS))
def test_cpp_templates_follow_conventions(kind: str) -> None:
    base, header, source = cpp_templates.render(kind, "MyThing", "MyGame")
    assert "GENERATED_BODY()" in header and f'#include "{base}.generated.h"' in header
    assert "MYGAME_API" in header and f'#include "{base}.h"' in source
    assert header.count("{") == header.count("}")


def test_cpp_name_validation_and_prefix() -> None:
    assert cpp_templates.render("actor", "AHero", "G")[0] == "Hero"
    with pytest.raises(ValueError):
        cpp_templates.render("actor", "bad name", "G")
    with pytest.raises(ValueError):
        cpp_templates.render("nope", "X", "G")


def _project(tmp_path: Path) -> dict:
    (tmp_path / "Source" / "MyGame" / "Public").mkdir(parents=True)
    (tmp_path / "Source" / "MyGame" / "Private").mkdir()
    (tmp_path / "Source" / "MyGame" / "MyGame.Build.cs").write_text("//")
    up = tmp_path / "MyGame.uproject"
    up.write_text(
        json.dumps({"EngineAssociation": "5.6", "Plugins": [{"Name": "PCG", "Enabled": False}]})
    )
    (tmp_path / "Saved" / "Logs").mkdir(parents=True)
    (tmp_path / "Saved" / "Logs" / "MyGame.log").write_text(
        "LogTemp: hi\nLogBlueprint: Error: broken pin\nLogX: Warning: meh\n"
    )
    return {
        "project_file": str(up),
        "project_dir": str(tmp_path),
        "engine_dir": str(tmp_path / "E"),
        "log_dir": str(tmp_path / "Saved" / "Logs"),
        "name": "MyGame",
    }


def test_create_cpp_class_writes_and_refuses_overwrite(tmp_path: Path) -> None:
    mcp, _ = _setup(_project(tmp_path))
    out = _call(mcp, "unreal_create_cpp_class", name="Door", kind="actor")
    assert out["success"] and out["result"]["verified"]
    assert (tmp_path / "Source/MyGame/Public/Door.h").is_file()
    assert (tmp_path / "Source/MyGame/Private/Door.cpp").is_file()
    again = _call(mcp, "unreal_create_cpp_class", name="Door", kind="actor")
    assert not again["success"] and again["error"]["code"] == "already_exists"
    missing = _call(mcp, "unreal_create_cpp_class", name="X", module="Nope")
    assert not missing["success"]


def test_plugin_toggle_with_backup(tmp_path: Path) -> None:
    mcp, _ = _setup(_project(tmp_path))
    assert not _call(mcp, "unreal_set_plugin_enabled", plugin="PCG")["success"]
    out = _call(mcp, "unreal_set_plugin_enabled", plugin="PCG", confirmed=True)
    assert (
        out["success"] and out["result"]["enabled"] is True and out["result"]["previous"] is False
    )
    assert (tmp_path / "MyGame.uproject.bak").is_file()
    listed = _call(mcp, "unreal_list_project_plugins")
    assert listed["result"]["declared"]["PCG"] is True


def test_output_log_filters(tmp_path: Path) -> None:
    mcp, _ = _setup(_project(tmp_path))
    out = _call(mcp, "unreal_get_output_log", severity="error")
    assert out["result"]["returned"] == 1 and "broken pin" in out["result"]["lines"][0]
    assert out["result"]["warnings"] == 1


def test_build_reports_missing_script(tmp_path: Path) -> None:
    mcp, _ = _setup(_project(tmp_path))
    out = _call(mcp, "unreal_build_project", confirmed=True)
    assert not out["success"] and out["error"]["code"] == "not_found"
