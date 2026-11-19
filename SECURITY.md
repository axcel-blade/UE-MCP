# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| `0.1.x` | Yes |
| `< 0.1` | No |

## Reporting a vulnerability

Do **not** open a public GitHub issue for security vulnerabilities.

Please report privately using one of:

1. GitHub **Security Advisories** for this repository (preferred)
2. Email the maintainers listed in [SUPPORT.md](SUPPORT.md) with subject `[SECURITY] Unreal Engine MCP`

Include:

- Description of the issue
- Steps to reproduce
- Affected versions / commit
- Potential impact
- Any suggested fix (optional)

We aim to acknowledge reports within **7 days** and provide a remediation plan or status update as soon as practical.

## Product security defaults

Unreal Engine MCP is designed for **trusted local development**:

- Bridge binds to `127.0.0.1` by default
- Safe mode restricts destructive and script-execution tools
- Optional shared auth token for the TCP bridge

See [docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md) for Safe vs Advanced mode details.

## Please do not

- Expose the TCP bridge to public networks
- Commit secrets, tokens, or credentials
- Request help weaponizing the bridge for unauthorized remote access
