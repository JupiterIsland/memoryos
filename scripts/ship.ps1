<#
.SYNOPSIS
    Zero-token safe verification, secret-scan, commit & push helper for MemoryOS // Jupiter Studio.
.EXAMPLE
    .\scripts\ship.ps1 "fix(studio): harden video spend lock"
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Message,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".git")) {
    throw "Run scripts/ship.ps1 from the MemoryOS repository root."
}

if (-not $SkipVerify) {
    Write-Host "[1/4] Running python -B verify.py --quick..." -ForegroundColor Cyan
    python -B verify.py --quick
    if ($LASTEXITCODE -ne 0) {
        throw "verify.py --quick failed — aborting commit."
    }
}

Write-Host "[2/4] Staging tracked & untracked repo files (excluding .env / SQLite)..." -ForegroundColor Cyan
git add -A
git reset -- .env QuietAdvisorDB.sqlite QuietAdvisorDB.sqlite-shm QuietAdvisorDB.sqlite-wal 2>$null | Out-Null

$staged = git --no-pager diff --cached --name-only
if (-not $staged) {
    Write-Host "Nothing to commit (working tree clean)." -ForegroundColor Yellow
    exit 0
}
if ($staged -contains ".env") {
    throw "ABORT: .env was staged! Refusing to commit."
}

Write-Host "[3/4] Running zero-secret leak gate against .env..." -ForegroundColor Cyan
$pyCheck = @'
import subprocess
from pathlib import Path
diff = subprocess.check_output(["git", "--no-pager", "diff", "--cached"], text=True, errors="replace")
env_p = Path(".env")
if env_p.exists():
    for line in env_p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, v = s.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if len(v) >= 8 and "your-" not in v and "http" not in v and "QuietAdvisorDB" not in v:
                if v in diff:
                    raise SystemExit(f"SECRET LEAK BLOCKED for key: {k.strip()}")
print("SECRET_LEAK_GATE: PASS")
'@
$pyCheck | python -B -
if ($LASTEXITCODE -ne 0) {
    throw "Secret leak gate blocked commit!"
}

Write-Host "[4/4] Committing and pushing to origin/main..." -ForegroundColor Cyan
git commit -m $Message
if ($LASTEXITCODE -ne 0) { throw "git commit failed." }
git push origin main
if ($LASTEXITCODE -ne 0) { throw "git push failed." }
Write-Host "[DONE] Shipped cleanly to origin/main." -ForegroundColor Green
