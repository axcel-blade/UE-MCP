"""Async length-prefixed TCP client."""

from __future__ import annotations

import asyncio
import json
import logging
import struct
from typing import Any

from mcp_server.core.protocol import BridgeRequest, BridgeResponse, encode_message
from mcp_server.exceptions import ConnectionError_, TimeoutError_

logger = logging.getLogger(__name__)


class TcpClient:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        connection_timeout: float = 10.0,
        request_timeout: float = 60.0,
        auth_token: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.connection_timeout = connection_timeout
        self.request_timeout = request_timeout
        self.auth_token = auth_token
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        if self.connected:
            return
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.connection_timeout,
            )
        except (TimeoutError, OSError) as exc:
            self._reader = None
            self._writer = None
            raise ConnectionError_(
                f"Could not connect to Unreal at {self.host}:{self.port}: {exc}. "
                "Ensure the UnrealEngineMCP plugin is loaded and the Editor is running."
            ) from exc
        logger.info("Connected to Unreal bridge %s:%s", self.host, self.port)

    async def disconnect(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError as exc:
                logger.debug("Error while closing Unreal TCP writer: %s", exc)
        self._writer = None
        self._reader = None

    async def ensure_connected(self) -> None:
        if not self.connected:
            await self.connect()

    async def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float | None = None,
        retry: bool = True,
    ) -> BridgeResponse:
        """Send one bridge request, reconnecting once if the peer dropped mid-call.

        ``timeout`` overrides the configured request timeout for this call. Pass
        ``retry=False`` for non-idempotent requests (such as running a script), which
        must not be resent after a dropped connection.
        """
        last_exc: Exception | None = None
        wait = timeout or self.request_timeout
        async with self._lock:
            for attempt in range(2 if retry else 1):
                await self.ensure_connected()
                assert self._reader is not None and self._writer is not None
                req = BridgeRequest(
                    method=method,
                    params=params or {},
                    auth=self.auth_token or None,
                )
                frame = encode_message(req)
                try:
                    self._writer.write(frame)
                    await self._writer.drain()
                    length_bytes = await asyncio.wait_for(self._reader.readexactly(4), timeout=wait)
                    (length,) = struct.unpack(">I", length_bytes)
                    body = await asyncio.wait_for(self._reader.readexactly(length), timeout=wait)
                except TimeoutError as exc:
                    await self.disconnect()
                    raise TimeoutError_(
                        f"Timed out waiting for Unreal response to {method}"
                    ) from exc
                except (asyncio.IncompleteReadError, ConnectionResetError, OSError) as exc:
                    await self.disconnect()
                    last_exc = exc
                    if attempt == 0 and retry:
                        logger.warning(
                            "Bridge dropped during %s; reconnecting once (%s)",
                            method,
                            exc,
                        )
                        continue
                    raise ConnectionError_(
                        f"Connection lost during {method}: {exc}. "
                        "Is the Unreal Editor still open with UnrealEngineMCP loaded "
                        f"on {self.host}:{self.port}?"
                    ) from exc

                data = json.loads(body.decode("utf-8"))
                return BridgeResponse.model_validate(data)

        raise ConnectionError_(
            f"Connection lost during {method}: {last_exc}. "
            "Is the Unreal Editor still open with UnrealEngineMCP loaded "
            f"on {self.host}:{self.port}?"
        )
