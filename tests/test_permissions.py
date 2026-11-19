"""Security permission unit tests."""

from __future__ import annotations

import pytest
from mcp_server.config import SecurityConfig, Settings
from mcp_server.core.permissions import assert_tool_allowed
from mcp_server.exceptions import PermissionError_


def test_safe_mode_allows_ping() -> None:
    settings = Settings(security=SecurityConfig(mode="safe"))
    assert_tool_allowed(settings, "unreal_ping")


def test_safe_mode_blocks_console() -> None:
    settings = Settings(security=SecurityConfig(mode="safe"))
    with pytest.raises(PermissionError_):
        assert_tool_allowed(settings, "unreal_execute_console_command")


def test_destructive_requires_confirmation() -> None:
    settings = Settings(
        security=SecurityConfig(mode="safe", require_confirmation_for_destructive_actions=True)
    )
    with pytest.raises(PermissionError_):
        assert_tool_allowed(settings, "unreal_delete_actor", confirmed=False)
    assert_tool_allowed(settings, "unreal_delete_actor", confirmed=True)
