"""Argument validation helpers."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from mcp_server.exceptions import ValidationError_

T = TypeVar("T", bound=BaseModel)


def validate_model(model: type[T], data: dict[str, Any]) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ValidationError_(str(exc)) from exc
