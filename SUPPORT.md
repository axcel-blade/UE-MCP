# Support

## How to get help

1. Read the docs:
   - [README.md](README.md)
   - Install site: [axcel-blade.github.io/UE-MCP](https://axcel-blade.github.io/UE-MCP/)
   - [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
   - [docs/INSTALLATION.md](docs/INSTALLATION.md)
   - [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Run diagnostics:

```powershell
uv sync
uv run python scripts/diagnose.py
uv run python scripts/test_connection.py
```

3. Search existing [GitHub Issues](../../issues) and [Discussions](../../discussions)
4. Open a new issue with the appropriate template
5. For questions / ideas, use Discussions (`Q_AND_A`, `IDEAS`)

## What to include

- OS and Unreal Engine version
- `unreal-engine-mcp` version (`uv run python -c "from mcp_server import __version__; print(__version__)"`)
- MCP client (Cursor, Claude Desktop, VS Code, …)
- Branch / commit
- Relevant logs (redact secrets)
- Whether the UnrealEngineMCP plugin loaded and which port it bound

## Security issues

Follow [SECURITY.md](SECURITY.md) — do not post exploit details publicly.

## Maintainers

- Organization / author: **AXCEL BLADE**
- Primary channel: GitHub Issues & Discussions for this repository
