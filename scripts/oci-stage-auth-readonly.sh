#!/usr/bin/env bash
# AEGIS OCI: expose ONLY two read-only authentication diagnostics through Caddy.
# No login/register POST, assessments, scans, administration, or documentation opened.
# No database modifications, customer mail, migrations, scheduler, or Vercel changes.
set -Eeuo pipefail
if [[ "$(id -u)" -eq 0 ]]; then
  echo "STOP: run this as the ubuntu SSH user, not root." >&2
  exit 1
fi
for unit in caddy aegis@api aegis@scanner aegis@intelligence aegis@notifier; do
  sudo systemctl is-active --quiet "$unit" || { echo "STOP: $unit is not active." >&2; exit 1; }
done

# First test the API directly on loopback. Parse the public Firebase web config
# in memory, NEVER print its values or the underlying service credentials.
python3 - <<'PY'
import json
from urllib.error import HTTPError
from urllib.request import urlopen
def get(path):
    try:
        with urlopen("http://127.0.0.1:8000"+path, timeout=9) as response:
            return response.status, response.read(4096)
    except HTTPError as error:
        return error.code, error.read(4096)
status, response = get("/auth/me")
if status != 401:
    raise SystemExit(f"STOP: expected unauthenticated /auth/me HTTP 401, got {status}.")
status, response = get("/auth/firebase/config")
if status != 200:
    raise SystemExit(f"STOP: expected public Firebase web config HTTP 200, got {status}.")
data=json.loads(response)
config=data.get("config")
if (data.get("enabled") is not True or not isinstance(config,dict)
    or config.get("projectId") != "aegis-d034c"
    or not all(isinstance(config.get(key),str) and config[key]
               for key in ("projectId","apiKey","appId","authDomain"))
    or "private_key" in config or "client_email" in config
    or config.get("emulatorUrl")):
    raise SystemExit("STOP: unexpected Firebase browser configuration; do not open gateway.")
print("AEGIS_AUTH_READONLY_INTERNAL_READY")
PY

current="$(sudo cat /etc/caddy/Caddyfile)"
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
if [[ "$current" == "$staged" ]]; then
  echo "AEGIS_AUTH_READONLY_STAGED: already configured."
  exit 0
fi
if [[ "$current" != "$expected" ]]; then
  echo "STOP: Caddyfile differs from the expected protected health-only gateway. Refusing to overwrite." >&2
  exit 1
fi
tmp="$(mktemp)"
backup=""
committed=0
restore() {
  if [[ "$committed" -ne 1 && -n "$backup" ]]; then
    echo "RESTORE: reverting to the previous health-only Caddy gateway." >&2
    sudo cp -p "$backup" /etc/caddy/Caddyfile
    sudo systemctl reload caddy || true
  fi
  rm -f "$tmp"
}
trap restore EXIT
printf '%s\n' "$staged" > "$tmp"
sudo caddy validate --adapter caddyfile --config "$tmp"
backup="/etc/caddy/Caddyfile.before-auth-readonly-$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp -p /etc/caddy/Caddyfile "$backup"
sudo install -o root -g root -m 0644 "$tmp" /etc/caddy/Caddyfile
sudo systemctl reload caddy

origin="https://aegis-pentest-eg-api.duckdns.org"
http_status() {
  curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 12 "$@"
}
me="$(http_status "$origin/auth/me")"
firebase="$(http_status "$origin/auth/firebase/config")"
health="$(http_status "$origin/health")"
login="$(http_status -X POST "$origin/auth/login")"
register="$(http_status -X POST "$origin/auth/register")"
admin="$(http_status "$origin/admin/connections")"
docs="$(http_status "$origin/openapi.json")"
if [[ "$me" != 401 || "$firebase" != 200 || "$health" != 200 ||
      "$login" != 503 || "$register" != 503 || "$admin" != 503 || "$docs" != 503 ]]; then
  echo "STOP: Caddy route acceptance failed. HTTP status summary:" >&2
  echo "/auth/me=$me /auth/firebase/config=$firebase /health=$health" >&2
  echo "POST /auth/login=$login POST /auth/register=$register /admin/connections=$admin /openapi.json=$docs" >&2
  exit 1
fi

# Verify that the newly reachable Firebase configuration has correct public metadata,
# without printing the API key or any other field from its response.
curl --fail --silent --show-error --max-time 12 "$origin/auth/firebase/config" |
python3 -c 'import sys,json; x=json.load(sys.stdin); assert x.get("enabled") is True and x.get("config",{}).get("projectId")=="aegis-d034c"'

committed=1
echo "AEGIS_AUTH_READONLY_STAGED"
echo "HTTPS GET /health and GET /auth/firebase/config work; GET /auth/me requires an existing session (401 without a cookie)."
echo "All POST login/register, customer operations and admin routes remain 503."
echo "No customer login, email, scan, scheduler, migrations, or Vercel deployment was performed."
