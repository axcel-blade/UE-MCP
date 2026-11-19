"""Protocol framing unit tests."""

from __future__ import annotations

import struct

from mcp_server.core.protocol import BridgeRequest, BridgeResponse, decode_frame, encode_message


def test_encode_decode_roundtrip() -> None:
    req = BridgeRequest(method="unreal_ping", params={"x": 1})
    frame = encode_message(req)
    assert frame[:4] == struct.pack(">I", len(frame) - 4)
    payload = decode_frame(frame[:4], frame[4:])
    assert payload["method"] == "unreal_ping"
    assert payload["params"]["x"] == 1


def test_bridge_response_model() -> None:
    resp = BridgeResponse(id="1", ok=True, result={"message": "pong"}, duration_ms=1.5)
    data = resp.model_dump(mode="json")
    assert data["ok"] is True
    assert data["result"]["message"] == "pong"
