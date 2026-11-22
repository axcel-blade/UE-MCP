"""Run editor Python in Unreal through the bridge and return structured results.

The user's code is wrapped in a small harness that runs it with ``unreal`` preloaded,
captures stdout, and reports the ``result`` variable (or the value of the last
expression), mirroring Blender-MCP's ``execute_blender_code``. The harness prints one
JSON line tagged with ``MARKER``; everything else the script prints is returned as
``stdout``.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp_server.core.response import fail, ok
from mcp_server.exceptions import UnrealEngineMCPError

logger = logging.getLogger(__name__)

MARKER = "@@UNREAL_MCP_RESULT@@"
BRIDGE_METHOD = "unreal_execute_editor_python"

_HARNESS = r"""
import ast as _ast, io as _io, json as _json, sys as _sys, traceback as _tb
import unreal
_src = {code!r}
_buf = _io.StringIO()
_ns = {{"unreal": unreal, "__name__": "__unreal_mcp__"}}
_payload = {{"ok": True}}
_old = _sys.stdout
try:
    _tree = _ast.parse(_src, "<unreal_mcp>", "exec")
    if _tree.body and isinstance(_tree.body[-1], _ast.Expr):
        _last = _tree.body.pop()
        _tree.body.append(_ast.Assign(targets=[_ast.Name("_mcp_last", _ast.Store())], value=_last.value))
        _ast.fix_missing_locations(_tree)
    _sys.stdout = _buf
    try:
        exec(compile(_tree, "<unreal_mcp>", "exec"), _ns)
    finally:
        _sys.stdout = _old
    _payload["result"] = _ns.get("result", _ns.get("_mcp_last"))
except BaseException:
    _sys.stdout = _old
    _payload = {{"ok": False, "error": _tb.format_exc(limit=8)}}
_payload["stdout"] = _buf.getvalue()[-20000:]
def _default(o):
    for attr in ("get_path_name", "get_name"):
        if hasattr(o, attr):
            try:
                return getattr(o, attr)()
            except Exception:
                pass
    if hasattr(o, "to_tuple"):
        return list(o.to_tuple())
    return str(o)
print({marker!r} + _json.dumps(_payload, default=_default))
"""


def build_harness(code: str) -> str:
    return _HARNESS.format(code=code, marker=MARKER)


def parse_bridge_result(result: dict[str, Any]) -> dict[str, Any]:
    """Turn the bridge's raw log lines into {ok, result, stdout, error}."""
    log = result.get("log") or []
    payload: dict[str, Any] | None = None
    other: list[str] = []
    for entry in log:
        text = entry.get("output", "") if isinstance(entry, dict) else str(entry)
        for line in text.splitlines():
            if line.startswith(MARKER):
                try:
                    payload = json.loads(line[len(MARKER) :])
                except json.JSONDecodeError:
                    payload = {"ok": False, "error": "Could not decode script result"}
            else:
                other.append(line)
    if payload is None:
        # Syntax errors in the harness itself or a crash before the marker printed.
        return {
            "ok": False,
            "error": "\n".join(other)[-4000:] or "Script produced no result",
            "stdout": "",
        }
    if other:
        payload["log"] = "\n".join(other)[-4000:]
    return payload


async def run_python(ctx: Any, code: str, *, timeout: float | None = None) -> dict[str, Any]:
    """Execute ``code`` in the editor; returns the standard {success, result|error} shape.

    Callers are responsible for permission checks. This talks to the client directly
    so curated tool packs can run vetted templates without enabling arbitrary Python.
    """
    params: dict[str, Any] = {"code": build_harness(code)}
    if timeout:
        params["timeout"] = max(1.0, min(float(timeout), 3600.0))
    try:
        wait = (params.get("timeout") or 60.0) + 15.0
        response = await ctx.dispatcher.client.request(
            BRIDGE_METHOD, params, timeout=wait, retry=False
        )
    except UnrealEngineMCPError as exc:
        return fail(exc.message, code=exc.code)
    except Exception as exc:
        logger.exception("Python execution failed")
        return fail(str(exc), code="unexpected_error")
    if not response.ok:
        err = response.error
        return fail(
            err.message if err else "Python execution failed",
            code=err.code if err else "engine_error",
        )
    payload = parse_bridge_result(response.result or {})
    if not payload.get("ok"):
        return fail(
            payload.get("error", "Script failed"),
            code="python_error",
            details={"stdout": payload.get("stdout", ""), "log": payload.get("log", "")},
        )
    data = {"result": payload.get("result"), "stdout": payload.get("stdout", "")}
    if payload.get("log"):
        data["log"] = payload["log"]
    return ok(data, duration_ms=response.duration_ms)
