#!/usr/bin/env bash
# One-time initialization of the AEGIS production PostgreSQL database on OCI.
# Does not expose any port, migrate schemas, deploy APIs or change Vercel/Windows.
set -Eeuo pipefail
trap 'echo "AEGIS database initialization stopped at line ${LINENO}; do NOT delete or reinitialize existing data." >&2' ERR
if [[ "$(id -u)" -eq 0 ]]; then echo 'Run as the ubuntu user, not root.' >&2; exit 1; fi
sudo systemctl is-active --quiet postgresql
sudo systemctl is-active --quiet redis-server
if [[ "$(redis-cli -h 127.0.0.1 PING)" != "PONG" ]]; then echo 'Redis health check failed.' >&2; exit 1; fi

# Refuse to initialize while PostgreSQL or Redis listen on external addresses.
for port in 5432 6379; do
  found=0
  while read -r proto recvq sendq addr peer rest; do
    case "$addr" in *:"$port") ;; *) continue ;; esac
    found=1
    case "$addr" in
      127.0.0.1:"$port"|"[::1]:"$port"|::1:"$port") ;;
      *) echo "Port $port is listening on $addr; restrict it to localhost first." >&2; exit 1 ;;
    esac
  done < <(sudo ss -lntH)
  if [[ "$found" -eq 0 ]]; then echo "Missing required listener on $port." >&2; exit 1; fi
done

# Fail closed rather than modifying an existing role or database.
if [[ "$(sudo -u postgres psql -XAtqc "SELECT count(*) FROM pg_roles WHERE rolname='aegis'" postgres)" != "0" ]] || \
   [[ "$(sudo -u postgres psql -XAtqc "SELECT count(*) FROM pg_database WHERE datname='aegis'" postgres)" != "0" ]]; then
  echo 'An aegis PostgreSQL role or database already exists. Aborting safely; inspect before proceeding.' >&2
  exit 1
fi

password="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
sudo install -d -m 0700 /etc/aegis
printf '%s\n' "$password" | sudo tee /etc/aegis/postgres-password >/dev/null
sudo chmod 0600 /etc/aegis/postgres-password
printf "CREATE ROLE aegis LOGIN PASSWORD '%s';\n" "$password" | sudo -u postgres psql -X -v ON_ERROR_STOP=1 -q postgres
sudo -u postgres createdb -O aegis aegis
if [[ "$(PGPASSWORD="$password" psql -X -h 127.0.0.1 -U aegis -d aegis -Atqc 'SELECT 1')" != "1" ]]; then
  echo 'Database login check failed. Do not re-run initialization.' >&2
  exit 1
fi
unset password
echo 'AEGIS_DB_READY: PostgreSQL database and limited application login created; local connectivity tested.'
echo 'Secret saved only on Oracle at /etc/aegis/postgres-password (root-readable). Do not share or upload it.'
echo 'No schema migration, API, background worker, public listener, or Vercel change has been performed.'
