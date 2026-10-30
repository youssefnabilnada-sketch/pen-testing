#!/usr/bin/env bash
# Opt-in: ensure validated AEGIS runtime survives Oracle VM reboot.
# Never starts scheduler or exposes new firewall/Caddy/HTTP routes.
set -Eeuo pipefail
if [[ "$(id -u)" -eq 0 ]]; then echo "Run as ubuntu, not root." >&2; exit 1; fi
for name in postgresql redis-server caddy aegis@api aegis@scanner aegis@intelligence aegis@notifier; do
  if ! sudo systemctl is-active --quiet "$name"; then
    echo "STOP: $name is not active. Do not enable unverified services." >&2; exit 1
  fi
done
if sudo systemctl is-active --quiet aegis@scheduler; then
  echo "STOP: scheduler unexpectedly running. Review before enabling persistence." >&2
  exit 1
fi
rev="$(sudo -u postgres psql -X -d aegis -Atqc 'SELECT version_num FROM alembic_version;' 2>/dev/null)"
if [[ "$rev" != 017_evidence_legal_holds ]]; then
  echo "STOP: database migration head differs; do not enable stale services." >&2
  exit 1
fi
curl --fail --silent --show-error --max-time 10 https://aegis-pentest-eg-api.duckdns.org/health |
  python3 -c 'import sys,json; assert json.load(sys.stdin).get("database")=="reachable"'
code="$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 12 -X POST https://aegis-pentest-eg-api.duckdns.org/auth/login)"
if [[ "$code" != 503 ]]; then
  echo "STOP: public account writes are not blocked (HTTP $code)." >&2;exit 1
fi
echo "Prerequisites passed; no scheduler or public account routes will be enabled."
if [[ "${1:-}" != --apply ]]; then
  echo "AEGIS_AUTOSTART_PREFLIGHT_PASS: dry run only. Re-run with --apply to enable autostart."
  exit 0
fi
for name in postgresql redis-server caddy aegis@api aegis@scanner aegis@intelligence aegis@notifier; do
  sudo systemctl enable "$name" >/dev/null
  sudo systemctl is-enabled --quiet "$name"
done
sudo systemctl disable aegis@scheduler >/dev/null 2>&1 || true
echo "AEGIS_AUTOSTART_ENABLED: database, Redis, Caddy and four running AEGIS roles."
echo "No services were restarted; scheduler remains disabled. No route was opened."
