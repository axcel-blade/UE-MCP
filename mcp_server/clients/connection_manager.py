"""Connection lifecycle helpers."""

from __future__ import annotations

from mcp_server.clients.tcp_client import TcpClient
from mcp_server.config import Settings


class ConnectionManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = TcpClient(
            settings.unreal.host,
            settings.unreal.port,
            connection_timeout=settings.unreal.connection_timeout,
            request_timeout=settings.unreal.request_timeout,
            auth_token=settings.unreal.auth_token,
        )

    async def connect(self) -> None:
        await self.client.connect()

    async def disconnect(self) -> None:
        await self.client.disconnect()

    @property
    def connected(self) -> bool:
        return self.client.connected
