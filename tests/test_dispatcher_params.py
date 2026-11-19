"""Dispatcher param normalization tests."""

from __future__ import annotations

from mcp_server.core.dispatcher import flatten_tool_params


def test_flatten_nested_params_from_cursor_host() -> None:
    raw = {
        "params": {
            "class_name": "StaticMeshActor",
            "name": "Cube",
            "location": {"x": 1, "y": 2, "z": 3},
        }
    }
    flat = flatten_tool_params(raw)
    assert flat["class_name"] == "StaticMeshActor"
    assert flat["name"] == "Cube"
    assert flat["location"]["z"] == 3
    assert "params" not in flat


def test_flatten_keeps_already_flat_params() -> None:
    raw = {"class_name": "StaticMeshActor", "name": "Sphere"}
    assert flatten_tool_params(raw) == raw


def test_flatten_merges_outer_keys_over_nested() -> None:
    raw = {"params": {"name": "inner"}, "name": "outer", "confirmed": True}
    flat = flatten_tool_params(raw)
    assert flat["name"] == "outer"
    assert flat["confirmed"] is True
