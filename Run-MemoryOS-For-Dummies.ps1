<#
.SYNOPSIS
    MemoryOS // The Quiet Advisor — "For Dummies" 1-Click Launcher (Windows)
.DESCRIPTION
    Zero-setup launcher locked onto Gemma-4-31B-IT (our flagship AMD Token Lab model).
    Seeds the demo database if needed, checks cloud status, and opens the dashboard.
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  MemoryOS // The Quiet Advisor (For Dummies Edition)" -ForegroundColor Cyan
Write-Host "  Flagship Model: Gemma-4-31B-IT (AMD Token Lab)     " -ForegroundColor White
Write-Host "=====================================================" -ForegroundColor Cyan

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[1/4] Created .env from .env.example (edit .env later to add API keys)." -ForegroundColor Yellow
} else {
    Write-Host "[1/4] Found .env configuration." -ForegroundColor Green
}

if (-not $env:MEMORYOS_DEFAULT_MODEL) { $env:MEMORYOS_DEFAULT_MODEL = "Gemma-4-31B-IT" }

if (-not (Test-Path "QuietAdvisorDB.sqlite")) {
    Write-Host "[2/4] Seeding showcase database (50 inferences, 7 cards, 20 checkpoints)..." -ForegroundColor Cyan
    python -B seed_gamer_showcase.py | Out-Null
} else {
    Write-Host "[2/4] Showcase database Ready (QuietAdvisorDB.sqlite)." -ForegroundColor Green
}

Write-Host "[3/4] Checking Gemma-4-31B-IT & Cloud Provider readiness..." -ForegroundColor Cyan
python -B -c "from src.memoryos.router import get_cloud_provider_status; s = get_cloud_provider_status(); print('      AMD Token Lab configured:', s['amd_tokenlab']['configured']); print('      DigitalOcean MI300X configured:', s['digitalocean_mi300x']['configured'])"

Write-Host "[4/4] Opening Quiet Advisor Dashboard at http://127.0.0.1:8765 ..." -ForegroundColor Green
Write-Host "      Press Ctrl+C in this window to stop the server." -ForegroundColor DarkGray
$dbPath = if ($env:QUIET_ADVISOR_DB) { $env:QUIET_ADVISOR_DB } else { "QuietAdvisorDB.sqlite" }
python -B apps\quiet_advisor_ui\server.py --host 127.0.0.1 --port 8765 --db $dbPath
