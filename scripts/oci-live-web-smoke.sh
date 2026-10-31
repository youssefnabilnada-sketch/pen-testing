#!/usr/bin/env bash
# Non-destructive Production frontend ↔ Oracle API smoke test.
# Use only AFTER the operator rotates the gateway key in Oracle and Vercel,
# and after the Vercel Production opt-in has been deliberately enabled.
# No login credentials, account creation, scans, reports or database writes.
set -Eeuo pipefail
origin=https://aegis-pentest-eg.vercel.app
backend=https://aegis-pentest-eg-api.duckdns.org
status() { curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 18 "$@"; }

expected() {
  local name="$1" got="$2" want="$3"
  if [[ "$got" == "$want" ]]; then
    printf 'PASS %-33s HTTP %s\n' "$name" "$got"
  else
    printf 'STOP %-33s HTTP %s (expected %s)\n' "$name" "$got" "$want" >&2
    exit 1
  fi
}
expected "Oracle direct health" "$(status "$backend/health")" 200
expected "Vercel proxied health" "$(status "$origin/api/health")" 200
expected "Vercel Firebase public config" "$(status "$origin/api/auth/firebase/config")" 200
expected "Vercel guest session" "$(status "$origin/api/auth/me")" 401
# This must hit input validation without touching the database or authenticating;
# a response of 503 here indicates that Next or Caddy gateway is still closed.
expected "Vercel gated auth route" \
 "$(status -X POST "$origin/api/auth/login" -H "Origin: $origin" \
 -H 'Content-Type: application/json' --data-binary '{}')" 422
# Prove absent/corrupt Origin cannot trigger a state-changing operation.
expected "Reject absent Origin" \
 "$(status -X POST "$origin/api/auth/login" -H 'Content-Type: application/json' --data-binary '{}')" 403
expected "Reject attacker Origin" \
 "$(status -X POST "$origin/api/auth/login" -H 'Origin: https://not-aegis.invalid' \
 -H 'Content-Type: application/json' --data-binary '{}')" 403
# Direct Oracle must never accept unauthenticated writes, even when
# Vercel's trusted server-to-server key is set.
expected "Oracle direct POST blocked" \
 "$(status -X POST "$backend/auth/login" -H 'Content-Type: application/json' --data-binary '{}')" 503
expected "Oracle direct business blocked" "$(status "$backend/organizations")" 503
echo 'AEGIS_PRODUCTION_SAFE_GATEWAY_SMOKE_PASS'
echo 'NOTE: this does NOT test Firebase user login, cookies, Brevo inbox, ownership, scans or FastFix.'
