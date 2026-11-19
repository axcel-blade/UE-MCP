"""Normalized tool response helpers."""

from __future__ import annotations

from typing import Any


def ok(result: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"success": True, "result": result or {}}
    payload.update(extra)
    return payload


def fail(
    message: str, *, code: str = "error", details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }
