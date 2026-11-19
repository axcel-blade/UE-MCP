"""Tool registration bookkeeping."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

ToolHandler = Callable[..., Awaitable[dict[str, Any]]]


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: ToolHandler
    category: str = "general"
    destructive: bool = False
    advanced_only: bool = False


@dataclass
class ToolRegistry:
    tools: dict[str, ToolSpec] = field(default_factory=dict)

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self.tools:
            raise ValueError(f"Duplicate tool registration: {spec.name}")
        self.tools[spec.name] = spec

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "destructive": t.destructive,
                "advanced_only": t.advanced_only,
            }
            for t in sorted(self.tools.values(), key=lambda x: x.name)
        ]
