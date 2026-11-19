"""Length-prefixed JSON bridge protocol (v1)."""

from __future__ import annotations

import json
import struct
import uuid
from typing import Any

from pydantic import BaseModel, Field

PROTOCOL_VERSION = "1.0"
MAX_MESSAGE_BYTES = 16 * 1024 * 1024  # 16 MiB


class BridgeRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str = PROTOCOL_VERSION
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
    auth: str | None = None


class BridgeError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class BridgeResponse(BaseModel):
    id: str
    ok: bool = True
    result: dict[str, Any] | None = None
    error: BridgeError | None = None
    duration_ms: float | None = None
    async_job_id: str | None = None


def encode_message(payload: dict[str, Any] | BaseModel) -> bytes:
    if isinstance(payload, BaseModel):
        body = payload.model_dump(mode="json", exclude_none=True)
    else:
        body = payload
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ValueError(f"Message exceeds max size ({len(raw)} > {MAX_MESSAGE_BYTES})")
    return struct.pack(">I", len(raw)) + raw


def decode_frame(length_bytes: bytes, body: bytes) -> dict[str, Any]:
    (length,) = struct.unpack(">I", length_bytes)
    if length != len(body):
        raise ValueError(f"Length mismatch: header={length} body={len(body)}")
    if length > MAX_MESSAGE_BYTES:
        raise ValueError("Message too large")
    return json.loads(body.decode("utf-8"))
