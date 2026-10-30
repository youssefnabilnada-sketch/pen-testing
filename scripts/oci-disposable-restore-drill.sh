#!/usr/bin/env bash
# Isolated, opt-in restore rehearsal of the live AEGIS PostgreSQL schema/data.
# Not a durable/encrypted backup service; do not retain the transient raw dump.
set -Eeuo pipefail
umask 077
if [[ "$(id -u)" -eq 0 ]]; then echo "Run as ubuntu, not root." >&2; exit 1; fi
# Oracle's sudoers may permit selected commands without a password while
# 'sudo -v' still demands one. Avoid global authentication renewal entirely.
# Instead, request PostgreSQL access noninteractively; fail closed if denied.
if ! db_bytes="$(sudo -n -u postgres psql -X -d aegis -Atqc 'SELECT pg_database_size(current_database());')"; then
  echo "STOP: PostgreSQL privilege check failed without a password. No dump or database was created." >&2
  echo "Check the specific sudoers rule for 'sudo -n -u postgres psql'; do not grant general passwordless root." >&2
  exit 1
fi
free_kb="$(df -Pk /var/lib/postgresql | awk 'NR==2 {print $4}')"
if ! [[ "$db_bytes" =~ ^[0-9]+$ && "$free_kb" =~ ^[0-9]+$ ]]; then
  echo "STOP: cannot safely estimate database size and disk availability." >&2; exit 1
fi
# A dump plus a second PostgreSQL database need free space; keep an extra GiB margin.
required_bytes=$((db_bytes * 3 + 1073741824))
free_bytes=$((free_kb * 1024))
if (( free_bytes <= required_bytes )); then
  echo "STOP: insufficient free disk space for isolated restore without risk to production." >&2
  exit 1
fi
if [[ "${1:-}" != --apply ]]; then
  echo "AEGIS_RESTORE_PREFLIGHT_PASS: enough disk estimated; no files or databases created."
  echo "Warning: --apply will briefly create a restricted raw dump and an isolated restored DB."
  exit 0
fi
workdir=""
testdb=""
db_created=0
cleanup() {
  trap - EXIT INT TERM
  if [[ "$db_created" == 1 && "$testdb" == aegis_restore_probe_* ]]; then
    sudo -n -u postgres dropdb --if-exists --force "$testdb" >/dev/null 2>&1 || echo "CHECK: isolated test DB needs manual cleanup." >&2
  fi
  if [[ -n "$workdir" && "$workdir" == /var/lib/postgresql/aegis-restore-test.* ]]; then
    sudo -n -u postgres rm -f "$workdir/backup.dump" || true
    sudo -n -u postgres rmdir "$workdir" || true
  fi
}
trap cleanup EXIT INT TERM
testdb="aegis_restore_probe_${RANDOM}_${RANDOM}"
workdir="$(sudo -n -u postgres mktemp -d /var/lib/postgresql/aegis-restore-test.XXXXXXXX)"
sudo -n -u postgres pg_dump -Fc --no-owner --file "$workdir/backup.dump" aegis
sudo -n -u postgres pg_restore --list "$workdir/backup.dump" >/dev/null
sudo -n -u postgres createdb --template=template0 "$testdb"
db_created=1
sudo -n -u postgres pg_restore --exit-on-error --no-owner --no-acl -d "$testdb" "$workdir/backup.dump"
source_tables="$(sudo -n -u postgres psql -X -d aegis -Atqc "SELECT count(*) FROM pg_tables WHERE schemaname='public';")"
restored_tables="$(sudo -n -u postgres psql -X -d "$testdb" -Atqc "SELECT count(*) FROM pg_tables WHERE schemaname='public';")"
source_rev="$(sudo -n -u postgres psql -X -d aegis -Atqc 'SELECT version_num FROM alembic_version;')"
restored_rev="$(sudo -n -u postgres psql -X -d "$testdb" -Atqc 'SELECT version_num FROM alembic_version;')"
if [[ -z "$source_rev" || "$source_rev" != "$restored_rev" || "$source_tables" != "$restored_tables" || "$restored_tables" == 0 ]]; then
  echo "STOP: restore schema counts/migration do not match; manual investigation needed." >&2
  exit 1
fi
echo "AEGIS_DISPOSABLE_RESTORE_PASS: isolated schema and Alembic head matched ($restored_tables tables)."
echo "Temporary restored database and raw dump will be deleted by cleanup."
echo "No live database was changed, and this does NOT establish encrypted backup retention."
