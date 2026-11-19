"""Structured exceptions for UnrealEngineMCP."""

from __future__ import annotations


class UnrealEngineMCPError(Exception):
    """Base error with machine-readable code."""

    def __init__(self, message: str, *, code: str = "unreal_engine_mcp_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ConnectionError_(UnrealEngineMCPError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="connection_error")


class TimeoutError_(UnrealEngineMCPError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="timeout")


class AuthError(UnrealEngineMCPError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="auth_failed")


class ValidationError_(UnrealEngineMCPError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class PermissionError_(UnrealEngineMCPError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="permission_denied")


class EngineError(UnrealEngineMCPError):
    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message, code="engine_error")
        self.details = details or {}
