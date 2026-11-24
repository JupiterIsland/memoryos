# Rotate-TokenLabKey.ps1
# Automated AMD Token Lab API key rotation
# Backs up old key, updates both TOKENLAB_API_KEY and TOKENLAB_BASE_URL, tests new key, logs rotation

param(
    [switch]$Force,
    [int]$RotationIntervalDays = 30
)

$ErrorActionPreference = "Stop"

# Locate repo root .env (works whether script is run from repo root or src\memoryos)
$candidateEnvPaths = @(
    (Join-Path $PSScriptRoot ".env"),
    (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) ".env")
)
$envPath = $candidateEnvPaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $envPath) {
    $envPath = Join-Path $PSScriptRoot ".env"
}

$rootDir = Split-Path -Parent $envPath
$envBackupDir = Join-Path $rootDir ".env-backups"
$logFile = Join-Path $rootDir ".tokenlab-rotations.log"
$lastRotationFile = Join-Path $rootDir ".last-rotation"

Write-Host "AMD Token Lab Key Rotation" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Step 1: Validate .env exists
if (-not (Test-Path $envPath)) {
    Write-Error "ERROR: .env not found at $envPath"
    exit 1
}

$envContent = @{}
Get-Content $envPath | ForEach-Object {
    if ($_ -match '^\s*([^=]+)\s*=\s*(.*)$' -and $_ -notmatch '^\s*#') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")
        $envContent[$key] = $value
    }
}

$oldKey = $envContent["TOKENLAB_API_KEY"]
if (-not $oldKey) {
    Write-Error "ERROR: TOKENLAB_API_KEY not found in $envPath"
    exit 1
}

$oldPrefix = if ($oldKey.Length -ge 10) { $oldKey.Substring(0, 10) } else { "tl-***" }
Write-Host "`nCurrent key: $oldPrefix..." -ForegroundColor Yellow

# Step 2: Check if rotation is needed
if ((Test-Path $lastRotationFile) -and -not $Force) {
    $lastRotation = [datetime](Get-Content $lastRotationFile)
    $daysSinceRotation = ([datetime]::Now - $lastRotation).Days
    $daysUntilRotation = $RotationIntervalDays - $daysSinceRotation

    if ($daysUntilRotation -gt 0) {
        Write-Host "OK Last rotated $daysSinceRotation days ago" -ForegroundColor Green
        Write-Host "   Next rotation recommended in $daysUntilRotation days (use -Force to rotate now)" -ForegroundColor Yellow
        exit 0
    }
}

# Step 3: Backup .env
if (-not (Test-Path $envBackupDir)) {
    New-Item -ItemType Directory -Path $envBackupDir | Out-Null
}

$backupName = ".env.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$backupPath = Join-Path $envBackupDir $backupName
Copy-Item $envPath $backupPath
Write-Host "OK Backed up to: $backupName" -ForegroundColor Green

# Step 4: Prompt for new key
Write-Host "`nManual Step: Generate New Key" -ForegroundColor Yellow
Write-Host "1. Visit your AMD Token Lab API Keys dashboard" -ForegroundColor White
Write-Host "2. Generate a new key (starts with 'tl-')" -ForegroundColor White
$newKey = (Read-Host "Paste new API Key").Trim()

if (-not $newKey -or -not $newKey.StartsWith("tl-") -or $newKey.Length -lt 12) {
    Write-Error "Invalid key format (must start with 'tl-')"
    exit 1
}

$newPrefix = $newKey.Substring(0, 10)
Write-Host "OK New key received: $newPrefix..." -ForegroundColor Green

# Step 5: Update .env with new key
$envFileContent = Get-Content $envPath -Raw
$envFileContent = $envFileContent -replace "(?m)^TOKENLAB_API_KEY=.*$", "TOKENLAB_API_KEY=$newKey"
Set-Content -Path $envPath -Value $envFileContent -NoNewline

Write-Host "OK Updated $envPath with new key" -ForegroundColor Green

# Step 6: Test new key against /chat/completions
Write-Host "`nTesting new key against AMD Token Lab..." -ForegroundColor Cyan

try {
    $apiBase = if ($envContent["TOKENLAB_BASE_URL"]) {
        $envContent["TOKENLAB_BASE_URL"]
    } elseif ($envContent["TOKENLAB_API_BASE"]) {
        $envContent["TOKENLAB_API_BASE"]
    } else {
        "https://api.tokenlab.amd.com/v1"
    }

    $headers = @{
        "Authorization" = "Bearer $newKey"
        "Content-Type"  = "application/json"
    }
    $testBody = @{
        model      = "MiniCPM5-2B"
        messages   = @(@{ role = "user"; content = "ping" })
        max_tokens = 4
    } | ConvertTo-Json -Depth 4

    $null = Invoke-RestMethod -Uri "$($apiBase.TrimEnd('/'))/chat/completions" -Method Post -Headers $headers -Body $testBody -TimeoutSec 15 -ErrorAction Stop
    Write-Host "OK New key verified successfully" -ForegroundColor Green
} catch {
    Write-Error "New key test failed: $_`nRestoring backup .env..."
    Copy-Item $backupPath $envPath
    exit 1
}

# Step 7: Log rotation (masked prefixes only)
$logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | Old: $oldPrefix... | New: $newPrefix... | Backup: $backupName"
Add-Content $logFile $logEntry
Set-Content $lastRotationFile (Get-Date).ToString("o")

Write-Host "`nKey Rotation Complete! Remember to revoke old key ($oldPrefix...) in the Token Lab console." -ForegroundColor Green

# Step 8: Optional Scheduled Task using New-ScheduledTaskTrigger
$scheduleChoice = Read-Host "`nSchedule automatic weekly rotation reminder? (y/n)"
if ($scheduleChoice -eq "y") {
    $taskExists = Get-ScheduledTask -TaskName "TokenLabKeyRotation" -ErrorAction SilentlyContinue
    if ($taskExists) {
        Write-Host "OK Task already scheduled" -ForegroundColor Green
    } else {
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

        Register-ScheduledTask -TaskName "TokenLabKeyRotation" `
            -Action $action `
            -Trigger $trigger `
            -Principal $principal `
            -Description "Rotate AMD Token Lab API key every Monday at 9am" `
            -Force | Out-Null

        Write-Host "OK Scheduled task created (runs every Monday at 9am)" -ForegroundColor Green
    }
}
