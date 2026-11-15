#!/usr/bin/env bash
# ==============================================================================
# MemoryOS // The Quiet Advisor - 1-Command DigitalOcean Cloud Deploy (Linux/WSL)
# Spins up or deploys to an Ubuntu Droplet using your registered Ed25519 SSH key
# Fingerprint: 75:f4:ca:fb:d4:b3:03:b4:34:8b:d2:68:f7:a4:95:dc (jupiterisland)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

REPO_URL="${MEMORYOS_GIT_URL:-https://github.com/JupiterIsland/memoryos.git}"
SSH_FINGERPRINT="75:f4:ca:fb:d4:b3:03:b4:34:8b:d2:68:f7:a4:95:dc"
DROPLET_NAME="${DO_DROPLET_NAME:-memoryos-quiet-advisor}"
DROPLET_REGION="${DO_DROPLET_REGION:-lon1}"
DROPLET_SIZE="${DO_DROPLET_SIZE:-s-1vcpu-1gb}"
DROPLET_IMAGE="${DO_DROPLET_IMAGE:-ubuntu-24-04-x64}"
CREATE_DROPLET=0
DROPLET_IP=""

usage() {
  cat <<'EOF'
Usage:
  ./installer/deploy-digitalocean.sh <DROPLET_IP>
  ./installer/deploy-digitalocean.sh --create-droplet [--region lon1] [--size s-1vcpu-1gb] [--name memoryos-quiet-advisor]

Environment / .env variables:
  DIGITALOCEAN_API_TOKEN   Required only for --create-droplet
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --create-droplet)
      CREATE_DROPLET=1
      shift
      ;;
    --region)
      DROPLET_REGION="${2:-lon1}"
      shift 2
      ;;
    --size)
      DROPLET_SIZE="${2:-s-1vcpu-1gb}"
      shift 2
      ;;
    --name)
      DROPLET_NAME="${2:-memoryos-quiet-advisor}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$DROPLET_IP" ]]; then
        DROPLET_IP="$1"
        shift
      else
        echo "[ERROR] Unexpected argument: $1" >&2
        usage
        exit 1
      fi
      ;;
  esac
done

# Safely read .env values without executing shell code or printing secrets
read_env_var() {
  local key="$1"
  local file="$2"
  [[ -f "$file" ]] || return 0
  python3 -B -c '
import sys
key, path = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            print(v.strip().strip("\"").strip("\x27").rstrip("\r"))
            break
' "$key" "$file"
}

if [[ -z "${DIGITALOCEAN_API_TOKEN:-}" ]]; then
  DIGITALOCEAN_API_TOKEN="$(read_env_var "DIGITALOCEAN_API_TOKEN" "$ENV_FILE")"
fi

if [[ "$CREATE_DROPLET" -eq 1 ]]; then
  if [[ -z "${DIGITALOCEAN_API_TOKEN:-}" || "$DIGITALOCEAN_API_TOKEN" == "dop_v1_your-digitalocean-api-token-here" ]]; then
    echo "[ERROR] DIGITALOCEAN_API_TOKEN is missing in .env or environment." >&2
    echo "        Add DIGITALOCEAN_API_TOKEN=\"dop_v1_...\" to .env, or pass an existing Droplet IP directly." >&2
    exit 1
  fi

  echo "[1/3] Creating Ubuntu 24.04 Droplet '$DROPLET_NAME' ($DROPLET_REGION / $DROPLET_SIZE)..."
  CREATE_RESP="$(curl -fsS -X POST "https://api.digitalocean.com/v2/droplets" \
    -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"$DROPLET_NAME\",
      \"region\": \"$DROPLET_REGION\",
      \"size\": \"$DROPLET_SIZE\",
      \"image\": \"$DROPLET_IMAGE\",
      \"ssh_keys\": [\"$SSH_FINGERPRINT\"],
      \"tags\": [\"memoryos\", \"quiet-advisor\", \"amd\"]
    }")"

  DROPLET_ID="$(printf '%s' "$CREATE_RESP" | python3 -B -c 'import sys, json; print(json.load(sys.stdin)["droplet"]["id"])')"
  echo "      Droplet ID: $DROPLET_ID — waiting for active public IPv4..."

  for _ in $(seq 1 40); do
    INFO_RESP="$(curl -fsS "https://api.digitalocean.com/v2/droplets/$DROPLET_ID" \
      -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN")"
    DROPLET_IP="$(printf '%s' "$INFO_RESP" | python3 -B -c '
import sys, json
d = json.load(sys.stdin)["droplet"]
if d.get("status") == "active":
    for n in d.get("networks", {}).get("v4", []):
        if n.get("type") == "public":
            print(n.get("ip_address", ""))
            break
')"
    if [[ -n "$DROPLET_IP" ]]; then
      break
    fi
    sleep 4
  done

  if [[ -z "$DROPLET_IP" ]]; then
    echo "[ERROR] Timed out waiting for Droplet public IPv4." >&2
    exit 1
  fi
  echo "      Active Public IPv4: $DROPLET_IP (waiting 12s for sshd)..."
  sleep 12
fi

if [[ -z "$DROPLET_IP" ]]; then
  echo "[ERROR] Provide a Droplet IP or --create-droplet." >&2
  usage
  exit 1
fi

# Locate Ed25519 key (handle WSL /mnt/c 0777 permissions safely via chmod 0600 temp copy)
RAW_KEY=""
for candidate in "$HOME/.ssh/id_ed25519" "/mnt/c/Users/RJMed/.ssh/id_ed25519"; do
  if [[ -f "$candidate" ]]; then
    RAW_KEY="$candidate"
    break
  fi
done

if [[ -z "$RAW_KEY" ]]; then
  echo "[ERROR] Could not find Ed25519 SSH private key at ~/.ssh/id_ed25519 or /mnt/c/Users/RJMed/.ssh/id_ed25519" >&2
  exit 1
fi

TMP_KEY="$(mktemp /tmp/do_ed25519_XXXXXX)"
cleanup() {
  rm -f "$TMP_KEY"
}
trap cleanup EXIT
cp "$RAW_KEY" "$TMP_KEY"
chmod 600 "$TMP_KEY"

echo "[2/3] Deploying MemoryOS Quiet Advisor UI to root@$DROPLET_IP ..."
ssh -i "$TMP_KEY" \
  -o StrictHostKeyChecking=accept-new \
  -o ConnectTimeout=15 \
  "root@$DROPLET_IP" \
  "REPO_URL='$REPO_URL' bash -s" <<'REMOTE_EOF'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -qq git python3 curl >/dev/null

if [[ -d /opt/memoryos/.git ]]; then
  git -C /opt/memoryos fetch --all --prune
  git -C /opt/memoryos reset --hard origin/main
else
  rm -rf /opt/memoryos
  git clone --depth 1 "$REPO_URL" /opt/memoryos
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
REMOTE_EOF

echo "[3/3] Deployment verified!"
echo "      Live Quiet Advisor URL: http://$DROPLET_IP/"
