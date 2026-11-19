"""Config loading tests."""

from __future__ import annotations

from mcp_server.config import load_settings


def test_load_default_config() -> None:
    settings = load_settings()
    assert settings.server.name == "UnrealEngineMCP"
    assert settings.unreal.port == 55557
    assert settings.security.mode == "safe"
