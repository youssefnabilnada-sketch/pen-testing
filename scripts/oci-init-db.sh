#!/usr/bin/env bash
# One-time initialization of AEGIS PostgreSQL on an OCI Ubuntu host.
# No public port, schema migration, API deployment, or Windows/Vercel change.
set -Eeuo pipefail
trap 'echo "AEGIS database initialization failed at line ${LINENO}; do not delete or reinitialize existing data." >&2' ERR

if [[ "$(id -u)" -eq 0 ]]; then
  echo 'Run as ubuntu (non-root); sudo is used only for host/database administration.' >&2
  exit 1
fi
sudo systemctl is-active --quiet postgresql
sudo systemctl is-active --quiet redis-server
if [[ "$(redis-cli -h 127.0.0.1 PING)" != 'PONG' ]]; then
  echo 'Redis health check failed.' >&2
  exit 1
fi

# Fail closed if databases/queues are externally reachable.
for port in 5432 6379; do
  found=0
  while read -r state recvq sendq address peer rest; do
    if [[ "$address" != *":$port" ]]; then
      continue
    fi
    found=1
    if [[ "$address" != "127.0.0.1:$port" && "$address" != "[::1]:$port" && "$address" != "::1:$port" ]]; then
      echo "STOP: port $port is listening on $address; restrict the service to loopback first." >&2
      exit 1
    fi
  done < <(sudo ss -lntH)
  if [[ "$found" -eq 0 ]]; then
    echo "STOP: required service is not listening on port $port." >&2
    exit 1
  fi
done

# Never overwrite existing database credentials or a previous role/database.
if sudo test -e /etc/aegis/postgres-password; then
  echo 'A credential file already exists; refusing to overwrite it. Check the earlier run.' >&2
  exit 1
fi
if [[ "$(sudo -u postgres psql -XAtqc "SELECT count(*) FROM pg_roles WHERE rolname='aegis'" postgres)" != '0' ]] || \
   [[ "$(sudo -u postgres psql -XAtqc "SELECT count(*) FROM pg_database WHERE datname='aegis'" postgres)" != '0' ]]; then
  echo 'An AEGIS role or database already exists. Refusing to modify existing data.' >&2
  exit 1
fi

password="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
sudo install -d -m 0700 -o root -g root /etc/aegis
sudo install -m 0600 -o root -g root /dev/null /etc/aegis/postgres-password
printf '%s\n' "$password" | sudo tee /etc/aegis/postgres-password >/dev/null
printf "CREATE ROLE aegis LOGIN PASSWORD '%s';\n" "$password" | sudo -u postgres psql -X -v ON_ERROR_STOP=1 -q postgres
sudo -u postgres createdb -O aegis aegis
if [[ "$(PGPASSWORD="$password" psql -X -h 127.0.0.1 -U aegis -d aegis -Atqc 'SELECT 1')" != '1' ]]; then
  echo 'Database login check failed. Inspect before retrying; do not recreate data.' >&2
  exit 1
fi
unset password
echo 'AEGIS_DB_READY: PostgreSQL login and database created; loopback connectivity tested.'
echo 'Secret saved on Oracle only: /etc/aegis/postgres-password (root-owned, mode 0600). Do not share it.'
echo 'No schema migrations, API, worker, public listener, or Vercel settings were changed.'
