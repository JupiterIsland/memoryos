<#
.SYNOPSIS
    1-Command DigitalOcean Cloud Deploy for MemoryOS // The Quiet Advisor UI.
.DESCRIPTION
    Deploys https://github.com/JupiterIsland/memoryos to an Ubuntu 24.04 DigitalOcean
    Droplet using your registered Ed25519 SSH key (jupiterisland:
    75:f4:ca:fb:d4:b3:03:b4:34:8b:d2:68:f7:a4:95:dc) and starts systemd on port 80.
.EXAMPLE
    .\installer\Deploy-DigitalOcean.ps1 -DropletIp 203.0.113.10
    .\installer\Deploy-DigitalOcean.ps1 -CreateDroplet
#>
[CmdletBinding()]
param(
    [string]$DropletIp = "",
    [switch]$CreateDroplet,
    [string]$DropletName = "memoryos-quiet-advisor",
    [string]$Region = "lon1",
    [string]$Size = "s-1vcpu-1gb",
    [string]$Image = "ubuntu-24-04-x64",
    [string]$RepoUrl = "https://github.com/JupiterIsland/memoryos.git"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$EnvFile = Join-Path $RepoRoot ".env"
$SshFingerprint = "75:f4:ca:fb:d4:b3:03:b4:34:8b:d2:68:f7:a4:95:dc"

function Get-DotEnvValue([string]$KeyName, [string]$Path) {
    if (-not (Test-Path $Path)) { return "" }
    foreach ($line in (Get-Content -Path $Path -Encoding UTF8)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) { continue }
        $parts = $trimmed.Split("=", 2)
        if ($parts[0].Trim() -eq $KeyName) {
            return $parts[1].Trim().Trim('"').Trim("'")
        }
    }
    return ""
}

if ($CreateDroplet) {
    $ApiToken = $env:DIGITALOCEAN_API_TOKEN
    if ([string]::IsNullOrWhiteSpace($ApiToken)) {
        $ApiToken = Get-DotEnvValue "DIGITALOCEAN_API_TOKEN" $EnvFile
    }
    if ([string]::IsNullOrWhiteSpace($ApiToken) -or $ApiToken -eq "dop_v1_your-digitalocean-api-token-here") {
        throw "DIGITALOCEAN_API_TOKEN is missing in .env or environment. Add it or pass -DropletIp directly."
    }

    Write-Host "[1/3] Creating Ubuntu 24.04 Droplet '$DropletName' ($Region / $Size)..." -ForegroundColor Cyan
    $Headers = @{
        "Authorization" = "Bearer $ApiToken"
        "Content-Type"  = "application/json"
    }
    $Payload = @{
        name     = $DropletName
        region   = $Region
        size     = $Size
        image    = $Image
        ssh_keys = @($SshFingerprint)
        tags     = @("memoryos", "quiet-advisor", "amd")
    } | ConvertTo-Json -Depth 4

    $BodyBytes = [System.Text.Encoding]::UTF8.GetBytes($Payload)
    $CreateResp = Invoke-RestMethod -Method Post -Uri "https://api.digitalocean.com/v2/droplets" -Headers $Headers -Body $BodyBytes
    $DropletId = $CreateResp.droplet.id
    Write-Host "      Droplet ID: $DropletId — waiting for active public IPv4..." -ForegroundColor DarkCyan

    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Seconds 4
        $Info = Invoke-RestMethod -Method Get -Uri "https://api.digitalocean.com/v2/droplets/$DropletId" -Headers $Headers
        if ($Info.droplet.status -eq "active") {
            $pubNet = $Info.droplet.networks.v4 | Where-Object { $_.type -eq "public" } | Select-Object -First 1
            if ($pubNet -and $pubNet.ip_address) {
                $DropletIp = $pubNet.ip_address
                break
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($DropletIp)) {
        throw "Timed out waiting for DigitalOcean Droplet public IPv4."
    }
    Write-Host "      Active Public IPv4: $DropletIp (waiting 12s for sshd)..." -ForegroundColor Green
    Start-Sleep -Seconds 12
}

if ([string]::IsNullOrWhiteSpace($DropletIp)) {
    throw "Provide -DropletIp <IP> or use -CreateDroplet."
}

$SshKeyPath = Join-Path $env:USERPROFILE ".ssh\id_ed25519"
if (-not (Test-Path $SshKeyPath)) {
    throw "Ed25519 SSH key not found at $SshKeyPath"
}

$RemoteScript = @'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 curl >/dev/null
if [ -d /opt/memoryos/.git ]; then
  git -C /opt/memoryos fetch --all --prune
  git -C /opt/memoryos reset --hard origin/main
else
  rm -rf /opt/memoryos
  git clone --depth 1 "__REPO_URL__" /opt/memoryos
fi
cd /opt/memoryos
python3 -B seed_gamer_showcase.py
cat >/etc/systemd/system/memoryos-quiet-advisor.service <<'UNIT'
[Unit]
Description=MemoryOS Quiet Advisor Live Telemetry Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/memoryos
ExecStart=/usr/bin/python3 -B /opt/memoryos/apps/quiet_advisor_ui/server.py --host 0.0.0.0 --port 80 --no-browser
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
Environment=QUIET_ADVISOR_DB=/opt/memoryos/QuietAdvisorDB.sqlite

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable memoryos-quiet-advisor.service >/dev/null 2>&1
systemctl restart memoryos-quiet-advisor.service
if command -v ufw >/dev/null 2>&1 && ufw status | grep -qi "Status: active"; then
  ufw allow 80/tcp >/dev/null 2>&1 || true
fi
sleep 2
curl -fsS "http://127.0.0.1:80/api/dashboard" >/dev/null
echo "REMOTE_DEPLOY_OK"
'@

$RemoteScript = ($RemoteScript -replace '__REPO_URL__', $RepoUrl) -replace "`r`n", "`n"

Write-Host "[2/3] Deploying MemoryOS Quiet Advisor UI to root@$DropletIp ..." -ForegroundColor Cyan
$RemoteScript | & ssh -i $SshKeyPath -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 "root@$DropletIp" "bash -s"
if ($LASTEXITCODE -ne 0) {
    throw "SSH remote deploy failed with exit code $LASTEXITCODE"
}

Write-Host "[3/3] Deployment verified!" -ForegroundColor Green
Write-Host "      Live Quiet Advisor URL: http://$DropletIp/" -ForegroundColor Yellow
