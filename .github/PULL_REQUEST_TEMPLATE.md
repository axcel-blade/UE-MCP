## Summary

<!-- What changed and why -->

## Git Flow

- [ ] Base branch is correct (`develop` for features, `main` for hotfixes/releases as appropriate)
- [ ] Branch naming follows `feature/*`, `release/*`, or `hotfix/*`

## Type of change

- [ ] Feature
- [ ] Bug fix
- [ ] Hotfix
- [ ] Documentation
- [ ] Refactor / chore
- [ ] Tests
- [ ] CI / CD / release

## Test plan

- [ ] `uv sync`
- [ ] `uv run pytest`
- [ ] `uv run ruff check mcp_server tests scripts`
- [ ] Manual Unreal Editor check (if applicable): plugin loads, bridge connects, tool works

## Security checklist

- [ ] No secrets committed
- [ ] No new public network exposure by default
- [ ] Destructive / script-execution behavior documented if changed

## Related issues

Closes #
