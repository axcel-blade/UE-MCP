# UnrealEngineMCP Windows installer (from a local clone)
# Installs uv if needed, syncs the project, and optional MCP client config.
# Save this file as UTF-8 without BOM. A BOM breaks Windows PowerShell 5.1 parsers.

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

Write-Host "UnrealEngineMCP installer for Windows" -ForegroundColor Cyan

function Ensure-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { return }
    Write-Host "Installing uv..."
    winget install --id=astral-sh.uv -e --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv not found after install. Open a new terminal and re-run."
    }
}

function Save-JsonNoBom([string]$Path, $Object) {
    $text = $Object | ConvertTo-Json -Depth 20
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $text + [Environment]::NewLine, $utf8NoBom)
}

Ensure-Uv
Set-Location $RepoRoot
Write-Host "Syncing project with uv (Python + deps from uv.lock)..."
uv sync

function Add-McpServer([string]$ConfigPath) {
    if (-not (Test-Path $ConfigPath)) { return $false }
    $backup = "$ConfigPath.ue-mcp.bak"
    Copy-Item $ConfigPath $backup -Force
    $json = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    if (-not $json.mcpServers) {
        $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue (@{}) -Force
    }
    $entry = [pscustomobject]@{
        command = "uv"
        args = @("run", "--directory", "$RepoRoot", "unreal-engine-mcp")
        env  = [pscustomobject]@{
            UNREAL_ENGINE_MCP_HOST = "127.0.0.1"
            UNREAL_ENGINE_MCP_PORT = "55557"
            UNREAL_ENGINE_MCP_SECURITY_MODE = "safe"
        }
    }
    $json.mcpServers | Add-Member -NotePropertyName unreal-engine-mcp -NotePropertyValue $entry -Force
    Save-JsonNoBom $ConfigPath $json
    Write-Host "Updated $ConfigPath (backup: $backup)"
    return $true
}

$cursor = Join-Path $env:USERPROFILE ".cursor\mcp.json"
$claude = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
[void](Add-McpServer $cursor)
[void](Add-McpServer $claude)

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host '1. uv run python scripts/install_plugin.py --project "D:\Path\To\YourProject.uproject"'
Write-Host "2. Open Unreal, enable UnrealEngineMCP and Editor Scripting Utilities, then compile/restart"
Write-Host "3. Restart your MCP client (Cursor / Claude Desktop)"
Write-Host "Done."
