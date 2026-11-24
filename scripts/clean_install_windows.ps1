<#
.SYNOPSIS
    Hardened transactional clean-install audit script for MemoryOS / Jupiter Studio v2.1.2 on Windows.
.DESCRIPTION
    Validates OS, Git, non-Store Python >= 3.11, creates an isolated .venv with rollback on failure,
    installs dependencies, bootstraps .env if absent, runs the 14-module CI test suite + NEON Control Plane validation + EWC anti-forgetting audit,
    verifies headless HTTP /api/health startup, and cleans up created artifacts on error.
#>
param(
    [int]$TestPort = 17861,
    [switch]$NonInteractive,
    [switch]$KeepVenv,
    [switch]$SelfTestNegativeChecks
)

$ErrorActionPreference = "Stop"
$CreatedItems = @()
$StudioProcess = $null

function Fail {
    param([string]$Message)
    Write-Host ""
    Write-Host "[FAILED] $Message" -ForegroundColor Red
    throw $Message
}

function Pass {
    param([string]$Message)
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Track-CreatedItem {
    param([string]$Path)
    if (Test-Path $Path) {
        $script:CreatedItems += $Path
    }
}

function Assert-ToolingValid {
    param(
        [string]$GitCommandPath,
        [string]$PythonCommandPath,
        [int]$Major,
        [int]$Minor
    )
    if ([string]::IsNullOrWhiteSpace($GitCommandPath)) {
        Fail "Git not installed or missing from PATH. Install Git for Windows first."
    }
    if ([string]::IsNullOrWhiteSpace($PythonCommandPath)) {
        Fail "Python not found on PATH. Install Python 3.11+ from https://www.python.org/downloads/."
    }
    if ($PythonCommandPath -like "*WindowsApps*") {
        Fail "Microsoft Store Python stub detected ($PythonCommandPath). Install standard Python 3.11+ with 'Add Python to PATH'."
    }
    if (($Major -lt 3) -or (($Major -eq 3) -and ($Minor -lt 11))) {
        Fail "Python 3.11+ is required (found $Major.$Minor)."
    }
}

function Cleanup-OnFailure {
    if ($CreatedItems.Count -eq 0) { return }
    Write-Warning "Rolling back newly created clean-install artifacts..."
    foreach ($item in $CreatedItems) {
        if (Test-Path $item) {
            try {
                Remove-Item $item -Recurse -Force
            } catch {
                Write-Warning "Could not remove ${item}: $_"
            }
        }
    }
}

if ($SelfTestNegativeChecks) {
    Write-Host "Running negative error-path validation (missing Git & Store Python stub)..." -ForegroundColor Cyan
    $caughtGit = $false
    try { Assert-ToolingValid -GitCommandPath "" -PythonCommandPath "C:\Python312\python.exe" -Major 3 -Minor 12 } catch { $caughtGit = $true }
    if (-not $caughtGit) { throw "Negative check failed: missing Git was not rejected" }

    $caughtStore = $false
    try { Assert-ToolingValid -GitCommandPath "C:\Program Files\Git\cmd\git.exe" -PythonCommandPath "C:\Users\Test\AppData\Local\Microsoft\WindowsApps\python.exe" -Major 3 -Minor 12 } catch { $caughtStore = $true }
    if (-not $caughtStore) { throw "Negative check failed: Microsoft Store Python stub was not rejected" }

    $caughtOldPy = $false
    try { Assert-ToolingValid -GitCommandPath "C:\Program Files\Git\cmd\git.exe" -PythonCommandPath "C:\Python310\python.exe" -Major 3 -Minor 10 } catch { $caughtOldPy = $true }
    if (-not $caughtOldPy) { throw "Negative check failed: Python 3.10 was not rejected" }

    Pass "Negative checks passed (missing Git, Store Python stub, and Python < 3.11 all fail closed cleanly)"
    exit 0
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Jupiter Studio v2.1.2 - Windows Clean Install Audit " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

try {
    $isWin = ($env:OS -eq "Windows_NT") -or $IsWindows
    if (-not $isWin) {
        Fail "This clean-install script targets Windows."
    }
    Pass "Windows OS detected"

    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    $gitSrc = if ($gitCmd) { $gitCmd.Source } else { "" }
    $pySrc = if ($pyCmd) { $pyCmd.Source } else { "" }

    $major = 0; $minor = 0
    if ($pySrc) {
        $verRaw = & $pySrc -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        $parts = $verRaw.Trim().Split('.')
        if ($parts.Length -ge 2) {
            $major = [int]$parts[0]
            $minor = [int]$parts[1]
        }
    }

    Assert-ToolingValid -GitCommandPath $gitSrc -PythonCommandPath $pySrc -Major $major -Minor $minor
    Pass "Git ($gitSrc) and Python $major.$minor ($pySrc) validated"

    if (-not (Test-Path ".git")) {
        Fail "Run this script from the MemoryOS repository root."
    }
    Pass "Repository root verified"

    $venvCreatedNow = $false
    if (-not (Test-Path ".venv-clean-audit")) {
        Write-Host "Creating isolated virtual environment (.venv-clean-audit)..." -ForegroundColor White
        & $pySrc -m venv ".venv-clean-audit"
        if (-not (Test-Path ".venv-clean-audit\Scripts\python.exe")) {
            Fail "Failed to create virtual environment."
        }
        $venvCreatedNow = $true
        Track-CreatedItem ".venv-clean-audit"
    }
    $venvPy = (Resolve-Path ".\.venv-clean-audit\Scripts\python.exe").Path
    Pass "Isolated virtual environment ready"

    if (Test-Path "requirements.txt") {
        & $venvPy -m pip install --upgrade pip --quiet
        & $venvPy -m pip install -r requirements.txt --quiet
        if ($LASTEXITCODE -ne 0) {
            Fail "pip install -r requirements.txt exited with $LASTEXITCODE"
        }
        Pass "Dependencies installed cleanly from requirements.txt"
    }

    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env"
        Track-CreatedItem ".env"
        Pass "Bootstrapped .env from .env.example"
    } else {
        Pass ".env configuration present"
    }

    Write-Host "`nRunning MemoryOS & Jupiter Studio v2.1.2 test suite..." -ForegroundColor Cyan
    $env:PYTHONPATH = "."
    & $venvPy -B -W error::DeprecationWarning -m unittest `
        tests/test_quiet_advisor_detectors.py `
        tests/test_jupiter_studio.py `
        tests/test_speculative_offload.py `
        tests/test_memory_keeper.py `
        tests/test_frank.py `
        tests/test_cross_silicon_profiles.py `
        tests/test_ops_console.py `
        tests/test_control_plane.py `
        tests/test_nvidia_telemetry_safety.py `
        tests/test_workspace_pack.py `
        tests/test_nvidia_brev_router.py `
        tests/test_heatstream.py `
        tests/test_grant_ledger_reconciliation.py `
        tests/test_offload_integrity.py `
        tests/test_cloud_video.py `
        tests/test_hf_hub.py
    if ($LASTEXITCODE -ne 0) {
        Fail "Unit test suite failed (exit code $LASTEXITCODE)."
    }
    Pass "All CI unit & HTTP tests passed"

    & $venvPy -B NEON_SINGLE_FILE.py
    if ($LASTEXITCODE -ne 0) {
        Fail "NEON Control Plane validation failed (exit code $LASTEXITCODE)."
    }
    Pass "NEON Control Plane certification passed (5/5)"

    $env:PYTHONPATH = ".;src"
    & $venvPy -B -m memoryos.memory_keeper audit | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Fail "EWC anti-forgetting audit failed."
    }
    Pass "EWC continual anti-forgetting audit passed"

    $portUsed = Get-NetTCPConnection -LocalPort $TestPort -ErrorAction SilentlyContinue
    if ($portUsed) {
        Fail "Test port $TestPort is already bound. Pass -TestPort <free_port>."
    }
    Pass "Port $TestPort is available"

    Write-Host "`nBooting Jupiter Studio on 127.0.0.1:$TestPort (--no-browser)..." -ForegroundColor Cyan
    $StudioProcess = Start-Process -FilePath $venvPy -ArgumentList "-B", "apps/jupiter_studio.py", "--no-browser", "--port", "$TestPort" -PassThru -WindowStyle Hidden

    $healthy = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 400
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$TestPort/api/health" -UseBasicParsing -TimeoutSec 2
            $json = $resp.Content | ConvertFrom-Json
            if ($resp.StatusCode -eq 200 -and $json.status -eq "ok") {
                $healthy = $true
                break
            }
        } catch {}
    }
    if (-not $healthy) {
        Fail "Jupiter Studio failed health check at http://127.0.0.1:$TestPort/api/health"
    }
    Pass "Live server /api/health check passed (status=ok, version=$($json.version))"

    if ($venvCreatedNow -and -not $KeepVenv) {
        Remove-Item ".venv-clean-audit" -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host " CLEAN INSTALL AUDIT PASSED (v2.1.2)                 " -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
} catch {
    Write-Host "`nINSTALL AUDIT FAILED: $_" -ForegroundColor Red
    Cleanup-OnFailure
    exit 1
} finally {
    if ($StudioProcess) {
        try {
            Stop-Process -Id $StudioProcess.Id -Force -ErrorAction SilentlyContinue
        } catch {}
    }
}
