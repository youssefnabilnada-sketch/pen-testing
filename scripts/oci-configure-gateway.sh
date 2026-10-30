#!/usr/bin/env bash
# Enable a public HTTPS gateway readiness page only; do NOT expose AEGIS API.
set -Eeuo pipefail
trap 'echo "Caddy HTTPS setup stopped at line ${LINENO}. Check the error; no API service was started." >&2' ERR

DOMAIN='aegis-pentest-eg-api.duckdns.org'
EXPECTED_IP='158.101.189.39'
if [[ "$(id -u)" == '0' ]]; then
  echo 'Run as the ubuntu user, not root.' >&2; exit 1
fi
actual_ip="$(getent ahostsv4 "$DOMAIN" | awk 'NR==1 {print $1}')"
if [[ "$actual_ip" != "$EXPECTED_IP" ]]; then
  echo "DNS mismatch: expected $EXPECTED_IP; got $actual_ip. Fix DuckDNS before continuing." >&2
  exit 1
fi
command -v caddy >/dev/null
sudo systemctl is-active --quiet caddy
# Only replace the exact Ubuntu packaged Caddy default. Its comments contain
# "reverse_proxy", which must NOT be treated as an active application route.
if sudo grep -Fq "$DOMAIN" /etc/caddy/Caddyfile; then
  echo 'The AEGIS hostname is already in Caddyfile. Inspect it before changing anything.' >&2
  exit 1
fi
active_config="$(sudo sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' /etc/caddy/Caddyfile | grep -vE '^($|#)' || true)"
expected_default=
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
cat > "$tmp" <<'CADDY'
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
sudo caddy validate --config "$tmp" --adapter caddyfile
backup="/etc/caddy/Caddyfile.before-aegis-$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp /etc/caddy/Caddyfile "$backup"
sudo install -o root -g root -m 0644 "$tmp" /etc/caddy/Caddyfile
if ! sudo systemctl reload caddy; then
  echo 'Reload failed; restoring original Caddyfile.' >&2
  sudo cp "$backup" /etc/caddy/Caddyfile
  sudo systemctl reload caddy || true
  exit 1
fi
echo 'AEGIS_TLS_GATEWAY_CONFIGURED: Caddy now requests HTTPS for the DuckDNS hostname.'
echo 'Only /gateway-check returns HTTP 200. All other paths return HTTP 503.'
echo 'No FastAPI, worker, database port, or production Vercel deployment was started.'
echo 'Use curl -i https://aegis-pentest-eg-api.duckdns.org/gateway-check to verify TLS reachability.'
echo 'If the check fails, inspect sudo journalctl -u caddy --no-pager -n 35 and OCI/OS firewalls.'
:80 {\nroot * /usr/share/caddy\nfile_server\n}'
if [[ "$active_config" != "$expected_default" ]]; then
  echo 'Caddyfile has custom active configuration; refusing to overwrite it.' >&2
  echo 'Only the packaged :80 static-file default may be replaced automatically.' >&2
  exit 1
fi
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
cat > "$tmp" <<'CADDY'
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
sudo caddy validate --config "$tmp" --adapter caddyfile
backup="/etc/caddy/Caddyfile.before-aegis-$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp /etc/caddy/Caddyfile "$backup"
sudo install -o root -g root -m 0644 "$tmp" /etc/caddy/Caddyfile
if ! sudo systemctl reload caddy; then
  echo 'Reload failed; restoring original Caddyfile.' >&2
  sudo cp "$backup" /etc/caddy/Caddyfile
  sudo systemctl reload caddy || true
  exit 1
fi
echo 'AEGIS_TLS_GATEWAY_CONFIGURED: Caddy now requests HTTPS for the DuckDNS hostname.'
echo 'Only /gateway-check returns HTTP 200. All other paths return HTTP 503.'
echo 'No FastAPI, worker, database port, or production Vercel deployment was started.'
echo 'Use curl -i https://aegis-pentest-eg-api.duckdns.org/gateway-check to verify TLS reachability.'
echo 'If the check fails, inspect sudo journalctl -u caddy --no-pager -n 35 and OCI/OS firewalls.'
