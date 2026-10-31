#!/usr/bin/env bash
# Stage AEGIS's native Linux runtime, WITHOUT starting any public services.
set -Eeuo pipefail
trap 'echo "AEGIS runtime staging stopped at line ${LINENO}. No database migration or public deployment was attempted." >&2' ERR

if [[ "$(id -u)" -eq 0 ]]; then
  echo 'Run as the ubuntu SSH user; do not run this script with sudo.' >&2
  exit 1
fi
source_dir="$HOME/aegis-cloud"
if [[ ! -f "$source_dir/scripts/server-process.py" ]]; then
  echo "Missing AEGIS source: $source_dir" >&2
  exit 1
fi
if [[ -e /srv/aegis/scripts/server-process.py ]]; then
  echo 'An AEGIS runtime already exists at /srv/aegis. Stop; do not overwrite it.' >&2
  exit 1
fi
if ! sudo test -f /etc/aegis/postgres-password; then
  echo 'The protected database password file is missing. Initialize the DB safely first.' >&2
  exit 1
fi
if [[ "$(uname -m)" != 'aarch64' ]]; then
  echo 'This script requires an ARM64 OCI A1 VM.' >&2
  exit 1
fi

echo '1/4 Staging committed AEGIS source to /srv/aegis (excluding Git and local secrets)...'
sudo install -d -m 0755 -o "$(id -un)" -g "$(id -gn)" /srv/aegis
git -C "$source_dir" archive HEAD | tar -x -C /srv/aegis
echo '2/4 Building a new Python environment in the final runtime location...'
(cd /srv/aegis && bash scripts/build-oci-backend.sh)
echo '3/4 Protecting code files and preparing distinct service identities...'
sudo chown -R root:root /srv/aegis
for role in api scanner intelligence notifier scheduler; do
  account="aegis-$role"
  if ! getent passwd "$account" >/dev/null; then
    sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$account"
  fi
done
sudo install -d -m 0755 -o root -g root /etc/aegis
echo '4/4 Installing systemd unit definitions WITHOUT enabling or starting them...'
sudo install -m 0644 /srv/aegis/infrastructure/deployment/aegis@.service /etc/systemd/system/aegis@.service
sudo install -m 0644 /srv/aegis/infrastructure/deployment/aegis-migrate.service /etc/systemd/system/aegis-migrate.service
sudo systemctl daemon-reload
echo 'AEGIS_RUNTIME_STAGED'
echo 'Installed source, Python dependencies, service identities and disabled service unit definitions.'
echo 'NOT DONE: env/secrets, production migrations, TLS hostname, API startup, worker startup, email, Firebase, Vercel or PC link.'
echo 'No local Docker volumes, Oracle DB schema, ingress rules or running Vercel services were modified.'
