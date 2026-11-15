# Start-AiderDeepSeek.ps1
# Launch Aider powered by DeepSeek-V4.1-Flash (AMD Token Lab / Local Ollama)
param(
    [string]$Task = "",
    [string[]]$Files = @("apps\jupiter_studio.py")
)

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Aider Coding Agent — DeepSeek-V4.1-Flash Mode" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Load .env
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^=]+)\s*=\s*(.*)$' -and $_ -notmatch '^\s*#') {
            $k = $matches[1].Trim()
            $v = $matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
        }
    }
}

$apiKey = $env:TOKENLAB_API_KEY
$apiBase = if ($env:TOKENLAB_BASE_URL) { $env:TOKENLAB_BASE_URL } else { "https://api.tokenlab.amd.com/v1" }

$env:OPENAI_API_KEY = $apiKey
$env:OPENAI_API_BASE = $apiBase

$aiderExe = (Get-Command aider -ErrorAction SilentlyContinue).Source
if (-not $aiderExe) {
    $fallback = Join-Path $env:USERPROFILE ".local\bin\aider.exe"
    if (Test-Path $fallback) {
        $aiderExe = $fallback
    } else {
        $fallback2 = Join-Path $env:LOCALAPPDATA "Programs\Python\Python*\Scripts\aider.exe"
        $aiderExe = Resolve-Path $fallback2 -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path
    }
}

if (-not $aiderExe) {
    Write-Error "ERROR: aider.exe not found in PATH or at $env:USERPROFILE\.local\bin\aider.exe"
    exit 1
}

$aiderCmd = @(
    $aiderExe,
    "--model", "openai/DeepSeek-V4.1-Flash",
    "--model-metadata-file", ".aider.model.metadata.json",
    "--model-settings-file", ".aider.model.settings.yml",
    "--no-auto-commits",
    "--stream"
)

if ($Files.Count -gt 0) {
    $aiderCmd += $Files
}

if ($Task) {
    $aiderCmd += @("--message", $Task)
}

Write-Host "`nConnecting Aider to DeepSeek-V4.1-Flash at $apiBase..." -ForegroundColor Green
& $aiderCmd[0] $aiderCmd[1..($aiderCmd.Length - 1)]
