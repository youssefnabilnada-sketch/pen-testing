#!/usr/bin/env bash
# Stage an AEGIS HTTPS API health probe through Caddy while keeping ALL business endpoints closed.
# This intentionally does NOT publish login, scanning, FastFix, admin, docs, or any other API routes.
set -Eeuo pipefail
if [[ "$(id -u)" -eq 0 ]]; then echo 'Run as the ubuntu user (not root).' >&2; exit 1; fi
for unit in caddy aegis@api aegis@scanner aegis@intelligence aegis@notifier; do
  if ! sudo systemctl is-active --quiet "$unit"; then
    echo "STOP: $unit is not active; no gateway change made." >&2; exit 1
  fi
done
python3 - <<'PY'
import json
from urllib.request import urlopen
for route in ('health','ready'):
    with urlopen(f'http://127.0.0.1:8000/{route}', timeout=10) as r:
        if r.status != 200:
            raise SystemExit(f'API {route}: HTTP {r.status}; no gateway change.')
        data=json.load(r)
    if route == 'health' and data.get('database') != 'reachable':
        raise SystemExit('API database is not reachable; no gateway change.')
    if route == 'ready' and data.get('ready') is not True:
        raise SystemExit('API /ready is not true; no gateway change.')
print('AEGIS_INTERNAL_API_READY')
PY
current="$(sudo cat /etc/caddy/Caddyfile)"
old="$(cat <<'CADDY'
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
staged="$(cat <<'CADDY'
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
    handle @health {
        reverse_proxy 127.0.0.1:8000
    }
    handle /gateway-check {
        respond "AEGIS HTTPS gateway is reachable. Only health diagnostics are public." 200
    }
    handle {
        respond "AEGIS API pending end-to-end acceptance; other routes remain closed." 503
    }
}
CADDY
)"
if [[ "$current" == "$staged" ]]; then
  echo 'AEGIS_CADDY_HEALTH_STAGED: already configured. Other API routes remain closed.'
  exit 0
fi
if [[ "$current" != "$old" ]]; then
  echo 'STOP: Current Caddyfile differs from expected temporary gateway; refusing overwrite.' >&2
  exit 1
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
printf '%s\n' "$staged" > "$tmp"
sudo caddy validate --config "$tmp" --adapter caddyfile
backup="/etc/caddy/Caddyfile.before-aegis-health-$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp -p /etc/caddy/Caddyfile "$backup"
sudo install -o root -g root -m 0644 "$tmp" /etc/caddy/Caddyfile
if ! sudo systemctl reload caddy; then
  echo 'Caddy reload failed; restoring previous config.' >&2
  sudo cp -p "$backup" /etc/caddy/Caddyfile
  sudo systemctl reload caddy || true
  exit 1
fi
if ! curl --silent --show-error --fail --max-time 20 https://aegis-pentest-eg-api.duckdns.org/health |
    python3 -c 'import json,sys; assert json.load(sys.stdin).get("database")=="reachable"'; then
  echo "Caddy remote health check failed; restoring previous config." >&2
  sudo cp -p "$backup" /etc/caddy/Caddyfile
  sudo systemctl reload caddy || true
  exit 1
fi
status="$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 12 https://aegis-pentest-eg-api.duckdns.org/auth/me)"
if [[ "$status" != '503' ]]; then
  echo "Unexpected public API route status $status; restoring previous config." >&2
  sudo cp -p "$backup" /etc/caddy/Caddyfile
  sudo systemctl reload caddy || true
  exit 1
fi
echo 'AEGIS_CADDY_HEALTH_STAGED'
echo 'HTTPS /health proxies to FastAPI; /gateway-check remains public. All other API routes return 503.'
echo 'No public accounts, scans, workers, scheduler, migrations or Vercel deployments changed.'
