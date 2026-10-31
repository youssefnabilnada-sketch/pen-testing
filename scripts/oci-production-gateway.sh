#!/usr/bin/env bash
# AEGIS v1: operator-approved PRODUCTION gateway. Never auto-enable Vercel.
# Usage (as ubuntu user): bash scripts/oci-production-gateway.sh --check|--install|--rollback
# KEY IS NEVER PRINTED, LOGGED, ACCEPTED AS A COMMAND ARGUMENT OR WRITTEN TO GIT.
set -Eeuo pipefail
umask 077

mode="$1"
case "$mode" in --check|--install|--rollback) ;; *) echo "Use --check, --install, or --rollback." >&2; exit 2;; esac
if [[ "$(id -u)" == 0 ]]; then echo "Run as the ubuntu user, not root." >&2; exit 1; fi

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
candidate="$repo_dir/infrastructure/deployment/Caddyfile.production-gated"
caddyfile=/etc/caddy/Caddyfile
envfile=/etc/aegis/caddy-production-gateway.env
dropin=/etc/systemd/system/caddy.service.d/90-aegis-production-gateway.conf
backup=/var/backups/aegis/production-gateway-v1
url=https://aegis-pentest-eg-api.duckdns.org

# The protected read-only gateway created by scripts/oci-stage-auth-readonly.sh.
# Do not replace a hand-edited or unexpectedly open gateway.
expected="$(cat <<'CADDY'
aegis-pentest-eg-api.duckdns.org {
    tls {
        issuer acme https://acme-v02.api.letsencrypt.org/directory
    }
    header {
        X-Content-Type-Options nosniff
        Referrer-Policy no-referrer
        -Server
    }
    @health {
        method GET
        path /health
    }
    @authReadOnly {
        method GET
        path /auth/me /auth/firebase/config
    }
    handle @health {
        reverse_proxy 127.0.0.1:8000
    }
    handle @authReadOnly {
        reverse_proxy 127.0.0.1:8000
    }
    handle /gateway-check {
        respond "AEGIS HTTPS gateway is reachable. Authentication write operations remain closed." 200
    }
    handle {
        respond "AEGIS authentication and business operations pending controlled acceptance." 503
    }
}
CADDY
)"

http_status() { curl -sS -o /dev/null -w '%{http_code}' --max-time 12 "$@"; }
require_services() {
  for service in postgresql redis-server caddy aegis@api aegis@scanner aegis@intelligence aegis@notifier; do
    sudo systemctl is-active --quiet "$service" ||
      { echo "STOP: inactive service $service" >&2; exit 1; }
  done
  if sudo systemctl is-active --quiet aegis@scheduler; then
    echo "STOP: scheduler must remain off pending approval." >&2; exit 1
  fi
}
require_base() {
  [[ -f "$candidate" ]] || { echo "STOP: approved Caddy template missing" >&2; exit 1; }
  local current
  current="$(sudo cat "$caddyfile")"
  [[ "$current" == "$expected" ]] ||
    { echo "STOP: deployed Caddy config differs from expected protected baseline; no change made." >&2; exit 1; }
  ! sudo test -e "$envfile" || { echo "STOP: production env file already exists." >&2; exit 1; }
  ! sudo test -e "$dropin" || { echo "STOP: Caddy gateway drop-in already exists." >&2; exit 1; }
  ! sudo test -e "$backup" || { echo "STOP: prior backup exists; review before retry." >&2; exit 1; }
}
require_closed_public() {
  [[ "$(http_status "$url/health")" == 200 ]] ||
    { echo "STOP: public health is not 200." >&2; exit 1; }
  [[ "$(http_status "$url/auth/firebase/config")" == 200 ]] ||
    { echo "STOP: Firebase public config is not 200." >&2; exit 1; }
  [[ "$(http_status "$url/auth/me")" == 401 ]] ||
    { echo "STOP: anonymous /auth/me is not 401." >&2; exit 1; }
  [[ "$(http_status -X POST "$url/auth/login")" == 503 ]] ||
    { echo "STOP: public account POST isn't blocked." >&2; exit 1; }
  [[ "$(http_status "$url/organizations")" == 503 ]] ||
    { echo "STOP: public business GET isn't blocked." >&2; exit 1; }
}

if [[ "$mode" == --rollback ]]; then
  sudo test -f "$backup/Caddyfile" ||
    { echo "STOP: saved Caddy baseline unavailable; no rollback performed." >&2; exit 1; }
  sudo cmp -s "$candidate" "$caddyfile" ||
    { echo "STOP: Caddy config was modified since installation; manual review required." >&2; exit 1; }
  sudo cp -p "$backup/Caddyfile" "$caddyfile"
  sudo rm -f "$dropin" "$envfile"
  sudo systemctl daemon-reload
  sudo systemctl restart caddy
  require_closed_public
  echo "AEGIS_PRODUCTION_GATEWAY_ROLLBACK_PASS — public writes blocked."
  echo "Vercel PRODUCTION opt-in must also be false."
  exit 0
fi

require_services
require_base
require_closed_public
if [[ "$mode" == --check ]]; then
  echo "AEGIS_PRODUCTION_GATEWAY_PREFLIGHT_PASS — Caddy is still closed."
  echo "Next: install only with an operator-owned production secret, then keep Vercel opt-in false until live tests."
  exit 0
fi

[[ -t 0 ]] ||
  { echo "STOP: interactive terminal required. Never pass secrets in argv/pipes." >&2; exit 1; }
read -r -s -p "Paste the dedicated 64-character Production gateway key (hidden): " key
printf '\n'
[[ "$key" =~ ^[A-Za-z0-9_-]{48,256}$ ]] ||
  { unset key; echo "STOP: invalid gateway key (48-256 URL-safe characters required)." >&2; exit 1; }
# Caddyfile environment replacement is validated before any system configuration changes.
sudo env AEGIS_PRODUCTION_GATEWAY_KEY="$key" caddy validate   --config "$candidate" --adapter caddyfile >/dev/null

applied=0
complete=0
restore_on_failure() {
  local rc="$?"
  trap - EXIT
  if [[ "$applied" == 1 && "$complete" != 1 ]]; then
    echo "ROLLBACK: restoring the protected read-only Caddy gateway." >&2
    sudo cp -p "$backup/Caddyfile" "$caddyfile" || true
    sudo rm -f "$dropin" "$envfile" || true
    sudo systemctl daemon-reload || true
    sudo systemctl restart caddy || true
  fi
  unset key || true
  exit "$rc"
}
trap restore_on_failure EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

sudo install -d -o root -g root -m 0700 "$backup"
sudo cp -p "$caddyfile" "$backup/Caddyfile"
applied=1
sudo install -d -o root -g root -m 0755 /etc/systemd/system/caddy.service.d
printf 'AEGIS_PRODUCTION_GATEWAY_KEY=%s\n' "$key" | sudo tee "$envfile" >/dev/null
sudo chown root:root "$envfile"
sudo chmod 0600 "$envfile"
printf '[Service]\nEnvironmentFile=%s\n' "$envfile" | sudo tee "$dropin" >/dev/null
sudo chown root:root "$dropin"
sudo chmod 0644 "$dropin"
sudo install -o root -g root -m 0644 "$candidate" "$caddyfile"
sudo systemctl daemon-reload
sudo systemctl restart caddy

# No customer login or writes: the valid-key test uses deliberately incomplete JSON.
require_closed_public
valid_status="$(http_status -X POST "$url/auth/login"   -H 'Content-Type: application/json'   -H 'Origin: https://aegis-pentest-eg.vercel.app'   -H "X-AEGIS-Preview-Gateway: $key"   --data-binary '{}')"
[[ "$valid_status" == 422 ]] ||
  { echo "STOP: keyed API routing did not return expected validation response." >&2; exit 1; }
[[ "$(http_status -X POST "$url/auth/login" -H 'Content-Type: application/json'   -H 'X-AEGIS-Preview-Gateway: definitely-wrong' --data-binary '{}')" == 503 ]] ||
  { echo "STOP: invalid gateway key was not rejected." >&2; exit 1; }
complete=1
unset key
echo "AEGIS_PRODUCTION_CADDY_GATEWAY_INSTALLED — public requests remain blocked."
echo "No Vercel flag was enabled, no users were created, no scans/migrations performed."
echo "Emergency rollback: bash scripts/oci-production-gateway.sh --rollback"
