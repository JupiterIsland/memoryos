# Start-AiderAMD.ps1
# Launch Aider + AMD Token Lab Dual-Brain Agent (Gemma-4-31B-IT Architect + Qwen3.8-27B Editor)
# Reads credentials from .env (supports repo root or current script folder)

param(
    [string]$Model = "Gemma-4-31B-IT",
    [string]$EditorModel = "Qwen3.8-27B",
    [string]$WeakModel = "MiniCPM5-2B",
    [switch]$SingleModel,
    [string]$Task = "",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AMD Token Lab Dual-Brain Aider Agent (MemoryOS v1.0)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Locate .env and repo root
$candidatePaths = @(
    (Join-Path $PSScriptRoot ".env"),
    (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) ".env")
)
$envPath = $candidatePaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $envPath) {
    Write-Error "ERROR: .env file not found. Create .env at repo root with TOKENLAB_API_KEY and TOKENLAB_BASE_URL."
    exit 1
}

$repoRoot = Split-Path -Parent $envPath
Set-Location $repoRoot

Write-Host "`nReading $envPath..." -ForegroundColor White
$env_dict = @{}
Get-Content $envPath | ForEach-Object {
    if ($_ -match '^\s*([^=]+)\s*=\s*(.*)$' -and $_ -notmatch '^\s*#') {
        $k = $matches[1].Trim()
        $v = $matches[2].Trim().Trim('"').Trim("'")
        $env_dict[$k] = $v
    }
}

# 2. Validate required variables
$apiKey = $env_dict["TOKENLAB_API_KEY"]
$apiBase = if ($env_dict["TOKENLAB_BASE_URL"]) {
    $env_dict["TOKENLAB_BASE_URL"]
} elseif ($env_dict["TOKENLAB_API_BASE"]) {
    $env_dict["TOKENLAB_API_BASE"]
} else {
    "https://api.tokenlab.amd.com/v1"
}

if (-not $apiKey) {
    Write-Error "ERROR: TOKENLAB_API_KEY not set in $envPath"
    exit 1
}

# 3. Mask the key for display
$maskedKey = if ($apiKey.Length -ge 14) {
    $apiKey.Substring(0, 10) + "..." + $apiKey.Substring($apiKey.Length - 4)
} else {
    "tl-***"
}

Write-Host "OK Found TOKENLAB_API_KEY : $maskedKey" -ForegroundColor Green
Write-Host "OK API Base               : $apiBase" -ForegroundColor Green
Write-Host "OK Architect Brain (31B)  : $Model" -ForegroundColor Green
Write-Host "OK Code Editor Brain (27B): $EditorModel" -ForegroundColor Green
Write-Host "OK Fast Scout Brain (2B)  : $WeakModel" -ForegroundColor Green

# 4. Lock Git identity to JupiterIsland so all Aider auto-commits credit JupiterIsland
git config user.name "Jupiter Island"
git config user.email "richardmurray2022@gmail.com"

# 5. Set environment variables for Aider & OpenAI-compatible tools
$env:OPENAI_API_BASE = $apiBase
$env:OPENAI_BASE_URL = $apiBase
$env:OPENAI_API_KEY = $apiKey
$env:OPENAI_MODEL_NAME = $Model
$env:TOKENLAB_API_KEY = $apiKey
$env:TOKENLAB_BASE_URL = $apiBase
$env:TOKENLAB_API_BASE = $apiBase
$env:TOKENLAB_MODEL = $Model

# 6. Ensure PATH includes ~/.local/bin and Python Scripts, and auto-install Aider if missing
$extraPaths = @(
    (Join-Path $HOME ".local\bin"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\Scripts"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\Scripts"),
    (Join-Path $env:APPDATA "Python\Python313\Scripts"),
    (Join-Path $env:APPDATA "Python\Python312\Scripts")
)
foreach ($p in $extraPaths) {
    if ((Test-Path $p) -and ($env:PATH -notlike "*$p*")) {
        $env:PATH = "$p;$env:PATH"
    }
}

if (-not (Get-Command aider -ErrorAction SilentlyContinue)) {
    Write-Host "`nAider is not installed yet. Installing Aider automatically via aider-install..." -ForegroundColor Yellow
    python -m pip install --upgrade aider-install
    $localBin = Join-Path $HOME ".local\bin"
    if ($env:PATH -notlike "*$localBin*") {
        $env:PATH = "$localBin;$env:PATH"
    }
    aider-install
    if (-not (Get-Command aider -ErrorAction SilentlyContinue)) {
        Write-Host "Falling back to direct pip install aider-chat..." -ForegroundColor Yellow
        python -m pip install --upgrade aider-chat
    }
}

if (-not (Get-Command aider -ErrorAction SilentlyContinue)) {
    Write-Error "ERROR: Aider installation could not be found on PATH. Run: python -m pip install aider-install; aider-install"
    exit 1
}

# 7. Core MemoryOS v1.0 files to attach to Aider's working context
$coreFiles = @(
    "src/memoryos/router.py",
    "src/memoryos/server.py",
    "src/memoryos/quiet_advisor_client.py",
    "apps/quiet_advisor_ui/api.py",
    "apps/quiet_advisor_ui/server.py",
    "apps/jupiter-tv-desktop-v2/app.py"
) | Where-Object { Test-Path (Join-Path $repoRoot $_) }

# 8. Launch Aider in Dual-Brain Architect Mode (Gemma-4-31B-IT + Qwen3.8-27B + MiniCPM5-2B)
if ($SingleModel) {
    Write-Host "`nLaunching Single-Model Aider with openai/$EditorModel..." -ForegroundColor Cyan
    if ($Task) {
        aider --model "openai/$EditorModel" --no-show-model-warnings --yes-always --message $Task @coreFiles
    } else {
        aider --model "openai/$EditorModel" --no-show-model-warnings @coreFiles
    }
} else {
    Write-Host "`nLaunching Dual-Brain Aider Architect (Gemma-4-31B-IT Architect + Qwen3.8-27B Editor)..." -ForegroundColor Cyan
    if ($Task) {
        aider --architect --model "openai/$Model" --editor-model "openai/$EditorModel" --weak-model "openai/$WeakModel" --no-show-model-warnings --yes-always --message $Task @coreFiles
    } else {
        aider --architect --model "openai/$Model" --editor-model "openai/$EditorModel" --weak-model "openai/$WeakModel" --no-show-model-warnings @coreFiles
    }
}
