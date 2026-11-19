# Communication Protocol v1.0

## Framing

```text
[uint32 big-endian length][UTF-8 JSON payload]
```

Maximum payload: 16 MiB.

## Request

```json
{
  "id": "uuid",
  "version": "1.0",
  "method": "unreal_ping",
  "params": {},
  "auth": "optional-shared-token"
}
```

## Response

```json
{
  "id": "uuid",
  "ok": true,
  "result": {},
  "duration_ms": 12.3
}
```

Error:

```json
{
  "id": "uuid",
  "ok": false,
  "error": {
    "code": "engine_error",
    "message": "Actor not found",
    "details": {}
  },
  "duration_ms": 4.1
}
```

## Common error codes

| Code | Meaning |
|---|---|
| `auth_failed` | Auth token mismatch |
| `protocol_error` | Invalid frame/JSON |
| `unsupported` | Method not implemented |
| `engine_error` | Unreal API failure |
| `compile_error` | Blueprint compile failed |
| `timeout` | Request timed out |
| `permission_denied` | Blocked by security mode |
