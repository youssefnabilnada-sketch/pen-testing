#!/usr/bin/env bash
# OCI production environment staging. No migration or service is started.
set -Eeuo pipefail
trap 'echo "AEGIS env staging stopped at line ${LINENO}; inspect existing files before retrying." >&2' ERR

if [[ "$(id -u)" -eq 0 ]]; then echo 'Run as the ubuntu user, not root.' >&2; exit 1; fi
if [[ ! -f /srv/aegis/infrastructure/deployment/production.env.example ]]; then echo 'Missing staged /srv/aegis runtime.' >&2; exit 1; fi
if ! sudo test -f /etc/aegis/postgres-password; then echo 'Protected database password missing.' >&2; exit 1; fi
for role in api scanner intelligence notifier scheduler; do
  account="aegis-$role"
  if ! getent passwd "$account" >/dev/null; then echo "Missing service user: $account" >&2; exit 1; fi
  if sudo test -e "/etc/aegis/$role.env"; then echo "Existing env: /etc/aegis/$role.env; refusing to overwrite." >&2; exit 1; fi
done
for role in api scanner intelligence notifier scheduler; do
  account="aegis-$role"
  if ! getent group "$account" >/dev/null; then
    sudo groupadd --system "$account"
    sudo usermod -g "$account" "$account"
  fi
done
password="$(sudo cat /etc/aegis/postgres-password)"
if [[ ! "$password" =~ ^[0-9a-f]{64}$ ]]; then echo 'Unexpected DB credential format.' >&2; exit 1; fi
fernet_key="$(/srv/aegis/.venv/bin/python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
firebase_public="$(grep -E '^FIREBASE_(PROJECT_ID|WEB_API_KEY|WEB_APP_ID)=' /srv/aegis/infrastructure/deployment/production.env.example)"
if [[ "$(wc -l <<< "$firebase_public")" -ne 3 ]]; then echo 'Missing Firebase public config.' >&2; exit 1; fi
sudo chown root:root /etc/aegis
sudo chmod 0711 /etc/aegis

write_env() {
  local role="$1"
  local path="/etc/aegis/$1.env"
  sudo install -o root -g "aegis-$role" -m 0640 /dev/null "$path"
  sudo tee "$path" >/dev/null
  sudo chmod 0640 "$path"
}
cat <<EOF | write_env api
AEGIS_ENV=production
DATABASE_URL=postgresql+psycopg://aegis:${password}@127.0.0.1:5432/aegis
REDIS_URL=redis://127.0.0.1:6379/0
WEB_ORIGIN=https://REPLACE-WITH-YOUR-VERCEL-ORIGIN.invalid
COOKIE_SECURE=true
LOCAL_FIXTURE_MODE=false
PAYMENTS_ENABLED=false
PRICING_ENABLED=false
PADDLE_ENABLED=false
INSTAPAY_ENABLED=false
AI_ASSISTANT_ENABLED=false
AI_PROVIDER_ENABLED=false
BILLING_MODE=disabled
DEMO_ACCESS_ENABLED=true
SMTP_HOST=REPLACE-WITH-REAL-SMTP.invalid
SMTP_PORT=587
SMTP_TLS=starttls
SMTP_USERNAME=REPLACE_ME
SMTP_PASSWORD=REPLACE_ME
MAIL_FROM=REPLACE_ME
FIREBASE_AUTH_ENABLED=true
${firebase_public}
GOOGLE_APPLICATION_CREDENTIALS=/etc/aegis/firebase-identity.json
MFA_ENCRYPTION_KEY=${fernet_key}
EOF
for role in scanner intelligence scheduler; do
  cat <<EOF | write_env "$role"
AEGIS_ENV=production
DATABASE_URL=postgresql+psycopg://aegis:${password}@127.0.0.1:5432/aegis
REDIS_URL=redis://127.0.0.1:6379/0
WEB_ORIGIN=https://REPLACE-WITH-YOUR-VERCEL-ORIGIN.invalid
COOKIE_SECURE=true
LOCAL_FIXTURE_MODE=false
PAYMENTS_ENABLED=false
PRICING_ENABLED=false
PADDLE_ENABLED=false
INSTAPAY_ENABLED=false
AI_ASSISTANT_ENABLED=false
AI_PROVIDER_ENABLED=false
BILLING_MODE=disabled
EOF
done
cat <<EOF | write_env notifier
AEGIS_ENV=production
DATABASE_URL=postgresql+psycopg://aegis:${password}@127.0.0.1:5432/aegis
REDIS_URL=redis://127.0.0.1:6379/0
WEB_ORIGIN=https://REPLACE-WITH-YOUR-VERCEL-ORIGIN.invalid
COOKIE_SECURE=true
LOCAL_FIXTURE_MODE=false
PAYMENTS_ENABLED=false
PRICING_ENABLED=false
PADDLE_ENABLED=false
INSTAPAY_ENABLED=false
AI_ASSISTANT_ENABLED=false
AI_PROVIDER_ENABLED=false
BILLING_MODE=disabled
SMTP_HOST=REPLACE-WITH-REAL-SMTP.invalid
SMTP_PORT=587
SMTP_TLS=starttls
SMTP_USERNAME=REPLACE_ME
SMTP_PASSWORD=REPLACE_ME
MAIL_FROM=REPLACE_ME
EOF
unset password fernet_key firebase_public
for role in api scanner intelligence notifier scheduler; do
  sudo -u "aegis-$role" test -r "/etc/aegis/$role.env"
done
if sudo -u aegis-scanner test -r /etc/aegis/api.env; then
  echo 'ERROR: scanner can read API identity secrets.' >&2; exit 1
fi
if sudo -u aegis-api test -r /etc/aegis/notifier.env; then
  echo 'ERROR: API can read notifier credentials.' >&2; exit 1
fi
echo 'AEGIS_ENV_STAGED: Separate secured service environments generated and verified.'
echo 'BLOCKED: HTTPS WEB_ORIGIN, SMTP provider, Firebase private credential and Caddy hostname still require configuration.'
echo 'NO migration, API start, worker start, Vercel deployment or public network changes were made.'
echo 'Never copy production .env contents into chat or GitHub.'
