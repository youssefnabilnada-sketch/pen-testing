#!/usr/bin/env bash
# Rotate the Oracle Caddy production gateway credential while public writes
# remain denied and Vercel's Production opt-in is FALSE.
# As ubuntu: bash scripts/oci-rotate-production-gateway.sh
# Never pass a secret via shell arguments, logs, chat or GitHub.
set -Eeuo pipefail
umask 077

[[ "$(id -u)" != 0 ]] || { echo 'STOP: run as ubuntu, not root.' >&2; exit 1; }
[[ -t 0 ]] || { echo 'STOP: requires interactive SSH terminal.' >&2; exit 1; }
envfile=/etc/aegis/caddy-production-gateway.env
caddyfile=/etc/caddy/Caddyfile
dropin=/etc/systemd/system/caddy.service.d/90-aegis-production-gateway.conf
url=https://aegis-pentest-eg-api.duckdns.org

http_status() { curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 15 "$@"; }
public_denied() {
  [[ "$(http_status "$url/health")" == 200 ]] || return 1
  [[ "$(http_status "$url/auth/firebase/config")" == 200 ]] || return 1
  [[ "$(http_status "$url/auth/me")" == 401 ]] || return 1
  [[ "$(http_status -X POST "$url/auth/login")" == 503 ]] || return 1
  [[ "$(http_status "$url/organizations")" == 503 ]] || return 1
}
for x in "$envfile" "$caddyfile" "$dropin"; do
  sudo test -f "$x" || { echo "STOP: expected installed gateway file missing." >&2; exit 1; }
  sudo test ! -L "$x" || { echo "STOP: unexpected symlink." >&2; exit 1; }
done
sudo test "$(sudo stat -c %a "$envfile")" = 600 ||
  { echo 'STOP: gateway credential file is not root-only 0600.' >&2; exit 1; }
sudo systemctl is-active --quiet caddy ||
  { echo 'STOP: Caddy is not active.' >&2; exit 1; }
# Before rotation ensure we have the reviewed release template, not a custom Caddy policy.
repo="$(cd "$(dirname "$0")/.." && pwd)"
sudo cmp -s "$repo/infrastructure/deployment/Caddyfile.production-gated" "$caddyfile" ||
  { echo 'STOP: installed Caddy config differs; manual review required.' >&2; exit 1; }
public_denied || { echo 'STOP: public deny preflight failed.' >&2; exit 1; }
echo 'AEGIS_GATEWAY_ROTATION_PREFLIGHT_PASS; Vercel Production opt-in must still be FALSE.'
echo 'Paste a NEW 64-character key generated and saved privately on Windows.'
read -r -s -p 'New dedicated Production gateway key (hidden): ' key
printf '\n'
[[ "$key" =~ ^[A-Za-z0-9_-]{64}$ ]] ||
  { unset key; echo 'STOP: new key must be exactly 64 URL-safe characters.' >&2; exit 1; }

# Do not expose either key in argv, shell history, process environment command
# arguments, Vercel logs, Caddy config, or HTTP URLs.
old="$(sudo mktemp /etc/aegis/.caddy-gateway-backup.XXXXXXXX)"
tmp="$(sudo mktemp /etc/aegis/.caddy-gateway-rotate.XXXXXXXX)"
sudo chmod 0600 "$old" "$tmp"
sudo cp -p "$envfile" "$old"
changed=0
complete=0
finish() {
  rc="$?"
  trap - EXIT
  if [[ "$complete" != 1 && "$changed" == 1 ]]; then
    echo 'ROLLBACK: restoring original Caddy secret; public writes stay denied.' >&2
    sudo cp -p "$old" "$envfile" || true
    sudo systemctl restart caddy || true
  fi
  sudo rm -f "$old" "$tmp" || true
  unset key || true
  exit "$rc"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Build root-only replacement and validate it before changing the live value.
printf 'AEGIS_PRODUCTION_GATEWAY_KEY=%s\n' "$key" | sudo tee "$tmp" >/dev/null
sudo chmod 0600 "$tmp"
sudo sh -c 'set -a; . "$1"; set +a; exec caddy validate --config "$2" --adapter caddyfile' \
  sh "$tmp" "$caddyfile" >/dev/null 2>&1 ||
  { echo 'STOP: replacement secret Caddy validation failed.' >&2; exit 1; }

sudo cp -p "$tmp" "$envfile"
changed=1
sudo systemctl restart caddy
public_denied ||
  { echo 'STOP: public-deny checks failed after rotation.' >&2; exit 1; }

# Use curl's secure header-on-stdin syntax; only invalid request shape, no
# customer login, account creation, or database mutation.
good="$(printf 'X-AEGIS-Preview-Gateway: %s\n' "$key" | \
  http_status -X POST "$url/auth/login" -H 'Content-Type: application/json' \
  -H 'Origin: https://aegis-pentest-eg.vercel.app' -H @- --data-binary '{}')"
[[ "$good" == 422 ]] ||
  { echo "STOP: new-key routing check returned unexpected HTTP $good." >&2; exit 1; }
[[ "$(http_status -X POST "$url/auth/login" -H 'X-AEGIS-Preview-Gateway: invalid' -H 'Content-Type: application/json' --data-binary '{}')" == 503 ]] ||
  { echo 'STOP: wrong-key rejection failed.' >&2; exit 1; }

complete=1
unset key
echo 'AEGIS_PRODUCTION_GATEWAY_ROTATED_PASS'
echo 'Public auth/business requests remain blocked without the new key.'
echo 'Update Vercel Production Secret to this SAME newly saved key; keep the opt-in FALSE until acceptance tests.'
