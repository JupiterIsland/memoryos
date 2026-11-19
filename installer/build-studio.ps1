<#
.SYNOPSIS
    Build standalone downloadable JupiterStudio.exe and JupiterStudio-Windows-x64.zip.
#>
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

Write-Host "[1/3] Checking PyInstaller..." -ForegroundColor Cyan
python -m PyInstaller --version | Out-Null

Write-Host "[2/3] Building standalone dist\JupiterStudio.exe..." -ForegroundColor Cyan
python -m PyInstaller --clean --noconfirm "installer\JupiterStudio.spec"

$ExePath = Join-Path $RepoRoot "dist\JupiterStudio.exe"
if (-not (Test-Path $ExePath)) {
    throw "Build failed: $ExePath not found."
}

Write-Host "[3/3] Packaging dist\JupiterStudio-Windows-x64.zip..." -ForegroundColor Cyan
$StageDir = Join-Path $RepoRoot "dist\JupiterStudio-Windows-x64"
if (Test-Path $StageDir) { Remove-Item -Recurse -Force $StageDir }
New-Item -ItemType Directory -Path $StageDir | Out-Null

Copy-Item $ExePath (Join-Path $StageDir "JupiterStudio.exe")
Copy-Item (Join-Path $RepoRoot ".env.example") (Join-Path $StageDir ".env.example")
Copy-Item (Join-Path $RepoRoot "README.md") (Join-Path $StageDir "README.md")
if (Test-Path (Join-Path $RepoRoot "LICENSE")) {
    Copy-Item (Join-Path $RepoRoot "LICENSE") (Join-Path $StageDir "LICENSE")
}

$ZipPath = Join-Path $RepoRoot "dist\JupiterStudio-Windows-x64.zip"
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $StageDir "*") -DestinationPath $ZipPath

$SizeMB = [Math]::Round((Get-Item $ZipPath).Length / 1MB, 2)
Write-Host "[OK] Built $ExePath and $ZipPath ($SizeMB MB)" -ForegroundColor Green
