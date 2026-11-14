# Start-AiderAMD.ps1
# Launch Aider with AMD Token Lab backend (Qwen3.8-27B)
# Reads credentials from .env (supports repo root or current script folder)

param(
    [string]$Model = "Qwen3.8-27B",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "AMD Token Lab Aider Launcher" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# 1. Locate .env (check script dir, then repo root two levels up)
$candidatePaths = @(
    (Join-Path $PSScriptRoot ".env"),
    (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) ".env")
)
$envPath = $candidatePaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $envPath) {
    Write-Error "ERROR: .env file not found. Create .env at repo root with TOKENLAB_API_KEY and TOKENLAB_BASE_URL."
    exit 1
}

Write-Host "`nReading $envPath..." -ForegroundColor White
$env_dict = @{}
Get-Content $envPath | ForEach-Object {
    if ($_ -match '^\s*([^=]+)\s*=\s*(.*)$' -and $_ -notmatch '^\s*#') {
        $k = $matches[1].Trim()
        $v = $matches[2].Trim().Trim('"').Trim("'")
        $env_dict[$k] = $v
    }
}

# 2. Validate required variables (accept TOKENLAB_BASE_URL or TOKENLAB_API_BASE)
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

$resolvedModel = if ($env_dict["TOKENLAB_MODEL"]) { $env_dict["TOKENLAB_MODEL"] } else { $Model }

# 3. Mask the key for display
$maskedKey = if ($apiKey.Length -ge 14) {
    $apiKey.Substring(0, 10) + "..." + $apiKey.Substring($apiKey.Length - 4)
} else {
    "tl-***"
}

Write-Host "OK Found TOKENLAB_API_KEY: $maskedKey" -ForegroundColor Green
Write-Host "OK API Base: $apiBase" -ForegroundColor Green
Write-Host "OK Model: $resolvedModel" -ForegroundColor Green

# 4. Set environment variables for Aider & OpenAI-compatible tools
$env:OPENAI_API_BASE = $apiBase
$env:OPENAI_BASE_URL = $apiBase
$env:OPENAI_API_KEY = $apiKey
$env:OPENAI_MODEL_NAME = $resolvedModel
$env:TOKENLAB_API_KEY = $apiKey
$env:TOKENLAB_BASE_URL = $apiBase
$env:TOKENLAB_API_BASE = $apiBase
$env:TOKENLAB_MODEL = $resolvedModel

# 5. Ensure PATH includes ~/.local/bin and Python Scripts, and auto-install Aider if missing
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

# 6. Test Token Lab connection via /chat/completions or /models
Write-Host "`nTesting AMD Token Lab connection..." -ForegroundColor Cyan
try {
    $headers = @{
        "Authorization" = "Bearer $apiKey"
        "Content-Type"  = "application/json"
    }
    $testBody = @{
        model      = $resolvedModel
        messages   = @(@{ role = "user"; content = "ping" })
        max_tokens = 4
    } | ConvertTo-Json -Depth 4

    $null = Invoke-RestMethod -Uri "$($apiBase.TrimEnd('/'))/chat/completions" -Method Post -Headers $headers -Body $testBody -TimeoutSec 15 -ErrorAction Stop
    Write-Host "OK Token Lab connection verified ($resolvedModel)" -ForegroundColor Green
} catch {
    Write-Warning "Token Lab preflight check warning: $_"
    Write-Host "Continuing to launch Aider..." -ForegroundColor Yellow
}

# 7. Launch Aider
Write-Host "`nLaunching Aider with openai/$resolvedModel..." -ForegroundColor Cyan
aider --model "openai/$resolvedModel"
