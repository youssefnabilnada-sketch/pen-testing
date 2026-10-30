#!/usr/bin/env bash
# Retry publicly trusted TLS via Let's Encrypt only. No AEGIS API is exposed.
set -Eeuo pipefail
trap 'echo "Caddy TLS setup stopped at line ${LINENO}; inspect before retrying." >&2' ERR

if [[ "$(id -u)" == '0' ]]; then echo 'Run as ubuntu, not root.' >&2; exit 1; fi
command -v caddy >/dev/null
sudo systemctl is-active --quiet caddy

expected="$(cat <<'CADDY'
aegis-pentest-eg-api.duckdns.org {
    header {
        X-Content-Type-Options nosniff
        Referrer-Policy no-referrer
        -Server
    }
    respond /gateway-check "AEGIS HTTPS gateway is reachable. Production API is not deployed." 200
    respond "AEGIS production API is not deployed." 503
}
CADDY
)"
existing="$(sudo cat /etc/caddy/Caddyfile)"
if [[ "$existing" != "$expected" ]]; then
  echo 'Current Caddyfile differs from the previous AEGIS gateway. Refusing to overwrite.' >&2
  exit 1
fi

site="$(cat <<'CADDY'
aegis-pentest-eg-api.duckdns.org {
    tls {
        issuer acme https://acme-v02.api.letsencrypt.org/directory
    }
    header {
        X-Content-Type-Options nosniff
        Referrer-Policy no-referrer
        -Server
    }
    respond /gateway-check "AEGIS HTTPS gateway is reachable. Production API is not deployed." 200
    respond "AEGIS production API is not deployed." 503
}
CADDY
)"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
printf '%s\n' "$site" > "$tmp"
sudo caddy validate --config "$tmp" --adapter caddyfile
backup="/etc/caddy/Caddyfile.before-letsencrypt-$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp -p /etc/caddy/Caddyfile "$backup"
sudo install -o root -g root -m 0644 "$tmp" /etc/caddy/Caddyfile
if ! sudo systemctl reload caddy; then
  echo 'Caddy reload failed. Restoring previous gateway configuration.' >&2
  sudo cp -p "$backup" /etc/caddy/Caddyfile
  sudo systemctl reload caddy || true
  exit 1
fi
echo 'AEGIS_LETSENCRYPT_RETRY_CONFIGURED'
echo 'Caddy will retry trusted TLS using Let-s Encrypt only.'
echo 'No production API, worker, database listener or Vercel deployment was started.'
echo 'Verify with: curl -i --max-time 30 https://aegis-pentest-eg-api.duckdns.org/gateway-check'
echo 'If TLS fails, inspect: sudo journalctl -u caddy -n 40 --no-pager'
