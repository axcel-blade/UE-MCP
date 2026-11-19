"""High-level Unreal bridge client."""

from __future__ import annotations

from typing import Any

from mcp_server.clients.connection_manager import ConnectionManager
from mcp_server.core.protocol import BridgeResponse


class UnrealClient:
    def __init__(self, connections: ConnectionManager) -> None:
        self._connections = connections

    @property
    def connected(self) -> bool:
        return self._connections.connected

    async def request(self, method: str, params: dict[str, Any] | None = None) -> BridgeResponse:
        return await self._connections.client.request(method, params)
