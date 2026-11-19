# Testing

## Python

```powershell
uv sync
uv run pytest
```

## Plugin

Compile UnrealEngineMCP with an Unreal project. Automation smoke tests can be added under `Private/Tests/`.

## Integration

Requires a temporary Unreal project. Never run destructive tests against production content.

```powershell
uv run python scripts/test_connection.py
```
