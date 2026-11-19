# Security

## Modes

### Safe (default)

- Read/inspect tools allowed
- Limited editing tools allowed (spawn, transform, save, materials, lighting, blueprints create/compile)
- Destructive tools require `confirmed=true`
- Python/console execution denied

### Advanced

- Enables additional mutation tools
- Python/console still require explicit config flags:
  - `security.allow_python_execution`
  - `security.allow_console_commands`

## Network

- Bind address defaults to `127.0.0.1`
- Optional shared `auth_token` checked by the plugin
- Do not expose the TCP port to public networks

## Path safety

File operations should stay within configured `paths.allowed_directories` when set.
