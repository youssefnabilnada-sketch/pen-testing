#!/usr/bin/env bash
# Configure a non-API, public HTTPS readiness endpoint for AEGIS.
set -Eeuo pipefail
trap 'echo "Caddy TLS gateway setup stopped at line ${LINENO}. No AEGIS service was started." >&2' ERR

DOMAIN='aegis-pentest-eg-api.duckdns.org'
EXPECTED_IP='158.101.189.39'
if [[ "$(id -u)" == '0' ]]; then echo 'Run as ubuntu, not root.' >&2; exit 1; fi
actual_ip="$(getent ahostsv4 "$DOMAIN" | awk 'NR==1 {print $1}')"
if [[ "$actual_ip" != "$EXPECTED_IP" ]]; then
  echo "DNS points to $actual_ip rather than Oracle $EXPECTED_IP; aborting." >&2
  exit 1
fi
command -v caddy >/dev/null
sudo systemctl is-active --quiet caddy

# Do not mistake the commented reverse_proxy in the Ubuntu default for an active proxy.
# Refuse to overwrite an active customized Caddy configuration.
active_config="$(sudo sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' /etc/caddy/Caddyfile | grep -vE '^($|#)' || true)"
expected_default="$(printf '%s\n' ':80 {' 'root * /usr/share/caddy' 'file_server' '}')"
if [[ "$active_config" != "$expected_default" ]]; then
  echo 'Caddyfile differs from the default static-file config; not overwriting.' >&2
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
sudo cp -p /etc/caddy/Caddyfile "$backup"
sudo install -o root -g root -m 0644 "$tmp" /etc/caddy/Caddyfile
if ! sudo systemctl reload caddy; then
  echo 'Caddy reload failed. Restoring original Caddyfile.' >&2
  sudo cp -p "$backup" /etc/caddy/Caddyfile
  sudo systemctl reload caddy || true
  exit 1
fi
echo 'AEGIS_TLS_GATEWAY_CONFIGURED: Caddy will obtain TLS for the DuckDNS hostname.'
echo 'Only /gateway-check responds 200. All other paths respond 503; API remains disabled.'
echo 'Verify: curl -i --max-time 20 https://aegis-pentest-eg-api.duckdns.org/gateway-check'
echo 'If TLS fails, inspect sudo journalctl -u caddy -n 35 --no-pager and network firewalls.'
