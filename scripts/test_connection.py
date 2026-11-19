#!/usr/bin/env python3
"""Smoke-test TCP connectivity to the Unreal bridge."""

from __future__ import annotations

import asyncio
import json

from mcp_server.clients.tcp_client import TcpClient
from mcp_server.config import load_settings


async def _run():
    settings = load_settings()
    client = TcpClient(
        settings.host,
        settings.port,
        auth_token=settings.unreal.auth_token,
        connection_timeout=settings.unreal.connection_timeout,
        request_timeout=settings.unreal.request_timeout,
    )
    try:
        resp = await client.request("unreal_ping", {})
        print(json.dumps(resp.model_dump(mode="json"), indent=2))
        return 0 if resp.ok else 1
    except (OSError, TimeoutError, ValueError, RuntimeError) as exc:
        print(f"FAILED: {exc}")
        return 1
    finally:
        await client.disconnect()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
