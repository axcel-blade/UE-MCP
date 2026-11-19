"""Configuration loaded from JSON + environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    name: str = "UnrealEngineMCP"
    transport: Literal["stdio"] = "stdio"
    log_level: str = "INFO"
    log_file: str | None = None


class UnrealBridgeConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 55557
    auto_connect: bool = True
    connection_timeout: float = 10.0
    request_timeout: float = 60.0
    auth_token: str = ""
    protocol_version: str = "1.0"


class SecurityConfig(BaseModel):
    mode: Literal["safe", "advanced"] = "safe"
    require_confirmation_for_destructive_actions: bool = True
    allow_python_execution: bool = False
    allow_console_commands: bool = False


class PathsConfig(BaseModel):
    project_directory: str = ""
    screenshot_directory: str = "output/screenshots"
    log_directory: str = "logs"
    allowed_directories: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UNREAL_ENGINE_MCP_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    unreal: UnrealBridgeConfig = Field(default_factory=UnrealBridgeConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

    @property
    def host(self) -> str:
        return self.unreal.host

    @property
    def port(self) -> int:
        return self.unreal.port


def _default_config_path() -> Path:
    env = os.environ.get("UNREAL_ENGINE_MCP_CONFIG")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1] / "config" / "config.json"


def load_settings(config_path: Path | None = None) -> Settings:
    path = config_path or _default_config_path()
    data: dict[str, Any] = {}
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))

    if host := os.environ.get("UNREAL_ENGINE_MCP_HOST"):
        data.setdefault("unreal", {})["host"] = host
    if port := os.environ.get("UNREAL_ENGINE_MCP_PORT"):
        data.setdefault("unreal", {})["port"] = int(port)
    if token := os.environ.get("UNREAL_ENGINE_MCP_AUTH_TOKEN"):
        data.setdefault("unreal", {})["auth_token"] = token
    if mode := os.environ.get("UNREAL_ENGINE_MCP_SECURITY_MODE"):
        data.setdefault("security", {})["mode"] = mode
    if level := os.environ.get("UNREAL_ENGINE_MCP_LOG_LEVEL"):
        data.setdefault("server", {})["log_level"] = level

    return Settings.model_validate(data)
