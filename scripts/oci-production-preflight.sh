#!/usr/bin/env bash
# Read-only AEGIS Oracle production preflight.
# Does not print credentials, change infrastructure, migrate, or start services.
set -uo pipefail
pass() { printf 'PASS    %s\n' "$1"; }
pending() { printf 'PENDING %s\n' "$1"; }
check() { printf 'CHECK   %s\n' "$1"; }

echo 'AEGIS OCI PRODUCTION PREFLIGHT (read-only; no secrets displayed)'
if [[ "$(id -u)" == 0 ]]; then
  check 'Run as ubuntu, not as root.'
  exit 1
fi

if sudo systemctl is-active --quiet postgresql && sudo systemctl is-active --quiet redis-server; then
  pass 'PostgreSQL and Redis services active.'
else
  check 'PostgreSQL or Redis service not active.'
fi
if sudo -u postgres psql -XAtqc "SELECT 1 FROM pg_database WHERE datname='aegis'" postgres 2>/dev/null | grep -qx 1; then
  pass 'AEGIS PostgreSQL database exists.'
else
  check 'AEGIS PostgreSQL database not confirmed.'
fi
if [[ -f /srv/aegis/scripts/server-process.py && -x /srv/aegis/.venv/bin/python ]]; then
  pass 'AEGIS code and Python runtime staged.'
else
  check 'AEGIS /srv runtime missing.'
fi
for role in api scanner intelligence notifier scheduler; do
  if sudo test -f "/etc/aegis/$role.env" && sudo -u "aegis-$role" test -r "/etc/aegis/$role.env"; then
    pass "Protected environment exists for $role."
  else
    check "Protected environment missing/inaccessible for $role."
  fi
done

if sudo systemctl is-enabled --quiet netfilter-persistent 2>/dev/null && \
    sudo grep -Fq -- '--dports 80,443' /etc/iptables/rules.v4 2>/dev/null; then
  pass 'Persistent network firewall saves HTTP/HTTPS allow rule.'
else
  check 'Firewall persistence is not fully verified. Do not reboot until corrected.'
fi
if curl --silent --fail --max-time 12 https://aegis-pentest-eg-api.duckdns.org/gateway-check | grep -q 'HTTPS gateway is reachable'; then
  pass 'Trusted HTTPS gateway reachable.'
else
  check 'HTTPS gateway is not responding as expected.'
fi

# Inspect presence and placeholders only. Never print environment file contents.
if sudo awk '/^WEB_ORIGIN=/{found=1; if ($0 ~ /^WEB_ORIGIN=https:\/\/[A-Za-z0-9.-]+$/ && $0 !~ /\.invalid$/) good=1} END{exit !(found && good)}' /etc/aegis/api.env; then
  pass 'WEB_ORIGIN is a non-placeholder HTTPS hostname.'
else
  pending 'Choose the exact Vercel public origin and configure it for all roles.'
fi

if sudo test -r /etc/aegis/firebase-identity.json; then
  pass 'Firebase service identity file present (connectivity NOT validated).'
else
  pending 'Install Firebase Admin service identity privately and limit file permissions.'
fi
if sudo awk '/^SMTP_HOST=/{found=1; if ($0 !~ /REPLACE|\.invalid$|localhost/ && $0 ~ /^SMTP_HOST=[A-Za-z0-9.-]+$/) good=1} END{exit !(found && good)}' /etc/aegis/api.env && \
    sudo grep -Eq '^SMTP_USERNAME=[^[:space:]]+' /etc/aegis/api.env && \
    ! sudo grep -Eq '^SMTP_USERNAME=REPLACE_ME$' /etc/aegis/api.env && \
    sudo grep -Eq '^SMTP_PASSWORD=[^[:space:]]+' /etc/aegis/api.env && \
    ! sudo grep -Eq '^SMTP_PASSWORD=REPLACE_ME$' /etc/aegis/api.env && \
    sudo grep -Eq '^MAIL_FROM=[^[:space:]]+@[^[:space:]]+$' /etc/aegis/api.env && \
    ! sudo grep -Eq '^MAIL_FROM=REPLACE_ME$' /etc/aegis/api.env; then
  pass 'API SMTP settings populated (SMTP connectivity NOT validated).'
else
  pending 'Configure real TLS SMTP credentials and sender in API + notifier environments.'
fi

if sudo grep -Fq 'respond /gateway-check' /etc/caddy/Caddyfile 2>/dev/null; then
  pending 'Caddy still serves the temporary gateway. API reverse proxy not enabled.'
else
  check 'Caddy gateway configuration differs from expected; inspect before changes.'
fi
if systemctl is-active --quiet aegis@api 2>/dev/null; then
  check 'API already running; inspect its status before any deployment action.'
else
  pending 'Production API not started.'
fi

echo 'AEGIS_PREFLIGHT_FINISHED'
echo 'No migrations, services, secrets, Caddy, GitHub production branch or Vercel project were changed.'
