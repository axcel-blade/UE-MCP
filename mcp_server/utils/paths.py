"""Path safety helpers."""

from __future__ import annotations

from pathlib import Path

from mcp_server.exceptions import ValidationError_


def assert_safe_path(path: str, allowed_roots: list[str]) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not allowed_roots:
        return resolved
    for root in allowed_roots:
        root_path = Path(root).expanduser().resolve()
        try:
            resolved.relative_to(root_path)
            return resolved
        except ValueError:
            continue
    raise ValidationError_(f"Path '{path}' is outside allowed directories")
