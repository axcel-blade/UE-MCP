"""Editor-Python backbone: safety checks, harness, result parsing and permissions."""

from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp_server import providers
from mcp_server.config import Settings
from mcp_server.core import python_exec
from mcp_server.security.script_safety import check
from mcp_server.tools.scripting.tools import editor_env, list_guides, read_guide


def _whats(code: str) -> list[str]:
    return [v.what for v in check(code)]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("import subprocess", "import subprocess"),
        ("import unreal\nunreal.SystemLibrary.quit_editor()", "unreal.SystemLibrary.quit_editor"),
        (
            "import unreal\nsl = unreal.SystemLibrary\nsl.launch_url('x')",
            "unreal.SystemLibrary.launch_url",
        ),
        ("import os\nos.remove('a')", "os.remove"),
        ("eval('1')", "eval"),
        ("x.__globals__", "__globals__"),
        (
            "import unreal\nunreal.EditorAssetLibrary.delete_directory('/Game')",
            "unreal.EditorAssetLibrary.delete_directory",
        ),
        (
            "import unreal\nunreal.SystemLibrary.execute_console_command(None, 'quit')",
            "unreal.SystemLibrary.execute_console_command",
        ),
    ],
)
def test_safety_refuses(code: str, expected: str) -> None:
    assert expected in _whats(code)


def test_safety_allows_normal_editor_code() -> None:
    code = (
        "eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)\n"
        "with unreal.ScopedEditorTransaction('x'):\n"
        "    a = eas.spawn_actor_from_class(unreal.PointLight, unreal.Vector(0, 0, 0))\n"
        "result = [x.get_actor_label() for x in eas.get_all_level_actors()]\n"
    )
    assert check(code) == []


def test_harness_is_valid_python_and_embeds_code_safely() -> None:
    tricky = "s = '''x'''\nresult = {\"a\": \"}\"}\n"
    harness = python_exec.build_harness(tricky)
    ast.parse(harness)  # must compile even with quotes/braces in user code
    assert repr(tricky) in harness


def test_parse_bridge_result_extracts_payload() -> None:
    payload = {"ok": True, "result": {"n": 3}, "stdout": "hi\n"}
    log = [
        {"type": "Info", "output": "noise"},
        {"type": "Info", "output": python_exec.MARKER + json.dumps(payload)},
    ]
    out = python_exec.parse_bridge_result({"log": log})
    assert out["result"] == {"n": 3}
    assert out["stdout"] == "hi\n"
    assert "noise" in out["log"]


def test_parse_bridge_result_without_marker_is_failure() -> None:
    out = python_exec.parse_bridge_result({"log": [{"type": "Error", "output": "SyntaxError"}]})
    assert out["ok"] is False
    assert "SyntaxError" in out["error"]


class _FakeResponse:
    def __init__(self, result: dict) -> None:
        self.ok = True
        self.result = result
        self.error = None
        self.duration_ms = 1.0


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict, dict]] = []

    async def request(self, method, params, **kw):
        self.calls.append((method, params, kw))
        line = python_exec.MARKER + json.dumps({"ok": True, "result": 42, "stdout": ""})
        return _FakeResponse({"log": [{"type": "Info", "output": line}]})


def _ctx(**security) -> SimpleNamespace:
    settings = Settings.model_validate({"security": security})
    client = _FakeClient()
    return SimpleNamespace(settings=settings, dispatcher=SimpleNamespace(client=client))


def test_run_python_never_retries_and_extends_timeout() -> None:
    ctx = _ctx()
    res = asyncio.run(python_exec.run_python(ctx, "1 + 1", timeout=120))
    assert res["success"] and res["result"]["result"] == 42
    method, _params, kw = ctx.dispatcher.client.calls[0]
    assert method == "unreal_execute_editor_python"
    assert kw["retry"] is False and kw["timeout"] > 120


def _execute(ctx: SimpleNamespace, **kwargs) -> dict:
    from mcp.server.fastmcp import FastMCP
    from mcp_server.tools.scripting import tools as scripting

    mcp = FastMCP("t")
    scripting.register(mcp, ctx)
    result = asyncio.run(mcp.call_tool("unreal_execute_python", kwargs))
    content = result[0] if isinstance(result, tuple) else result
    return json.loads(content[0].text)


def test_execute_python_disabled_by_default() -> None:
    out = _execute(_ctx(mode="advanced"), code="1")
    assert out["success"] is False and "disabled" in out["error"]["message"]


def test_execute_python_requires_confirmation_then_runs() -> None:
    ctx = _ctx(mode="advanced", allow_python_execution=True)
    assert _execute(ctx, code="1")["error"]["code"] == "confirmation_required"
    assert _execute(ctx, code="1", confirmed=True)["result"]["result"] == 42


def test_execute_python_refuses_unsafe_before_running() -> None:
    ctx = _ctx(mode="advanced", allow_python_execution=True, script_permission="trusted")
    out = _execute(ctx, code="import subprocess")
    assert out["error"]["code"] == "unsafe_script"
    assert ctx.dispatcher.client.calls == []


def test_guides_exist() -> None:
    names = list_guides()
    for name in ("unreal_python", "games", "film", "live_events", "automotive", "simulation"):
        assert name in names
        assert read_guide(name).startswith("#")


def test_editor_env_fills_windows_essentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    for key in ("SystemRoot", "LOCALAPPDATA", "TEMP"):
        monkeypatch.delenv(key, raising=False)
    env = editor_env()
    assert env["SystemRoot"] and env["LOCALAPPDATA"] and env["TEMP"]


def test_provider_paths_reject_traversal(tmp_path: Path) -> None:
    with pytest.raises(providers.ProviderError):
        providers.safe_join(tmp_path, "../evil.txt")
    with pytest.raises(providers.ProviderError):
        providers.safe_join(tmp_path, "C:/evil.txt")
    assert providers.safe_join(tmp_path, "a/b.png").is_relative_to(tmp_path.resolve())


def test_provider_requires_keys() -> None:
    cfg = Settings().providers
    with pytest.raises(providers.ProviderError):
        providers._require(cfg, "sketchfab")
    providers._require(cfg, "polyhaven")
