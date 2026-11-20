"""TcpClient reconnects once when the bridge drops mid-request."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_server.clients.tcp_client import TcpClient
from mcp_server.core.protocol import BridgeResponse, encode_message
from mcp_server.exceptions import ConnectionError_


def _ok_frame() -> list[bytes]:
    frame = encode_message(BridgeResponse(id="x", ok=True, result={"pong": True}))
    return [frame[:4], frame[4:]]


def _mock_writer() -> MagicMock:
    writer = MagicMock()
    writer.is_closing.return_value = False
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return writer


@pytest.mark.asyncio
async def test_request_reconnects_once_after_incomplete_read() -> None:
    client = TcpClient("127.0.0.1", 55557, connection_timeout=1.0, request_timeout=1.0)

    reader1 = AsyncMock()
    writer1 = _mock_writer()
    reader1.readexactly = AsyncMock(side_effect=asyncio.IncompleteReadError(b"", 4))

    reader2 = AsyncMock()
    writer2 = _mock_writer()
    reader2.readexactly = AsyncMock(side_effect=_ok_frame())

    connect_calls = {"n": 0}

    async def fake_open(host, port):
        connect_calls["n"] += 1
        if connect_calls["n"] == 1:
            return reader1, writer1
        return reader2, writer2

    with patch("mcp_server.clients.tcp_client.asyncio.open_connection", side_effect=fake_open):
        result = await client.request("unreal_ping", {})

    assert result.ok is True
    assert result.result == {"pong": True}
    assert connect_calls["n"] == 2
    await client.disconnect()


@pytest.mark.asyncio
async def test_request_raises_after_second_drop() -> None:
    client = TcpClient("127.0.0.1", 55557, connection_timeout=1.0, request_timeout=1.0)

    async def always_drop(host, port):
        reader = AsyncMock()
        writer = _mock_writer()
        reader.readexactly = AsyncMock(side_effect=asyncio.IncompleteReadError(b"", 4))
        return reader, writer

    with (
        patch("mcp_server.clients.tcp_client.asyncio.open_connection", side_effect=always_drop),
        pytest.raises(ConnectionError_, match="Connection lost during unreal_ping"),
    ):
        await client.request("unreal_ping", {})

    await client.disconnect()
