#!/bin/sh
# Run only inside the ephemeral CI PostgreSQL service, never on a live database.
set -eu
[ "${AEGIS_DISPOSABLE_RESTORE:-}" = "ci-fixture-only" ] || exit 2
[ "${POSTGRES_DB:-}" = "aegis" ] && [ "${POSTGRES_USER:-}" = "aegis" ] || exit 2
export PGUSER=aegis
backup=$(mktemp)
trap 'rm -f "$backup"' EXIT
# This table contains synthetic data only; migrations have already run in CI.
psql -X -v ON_ERROR_STOP=1 -d aegis <<'SQL'
CREATE TABLE restore_acceptance_fixture (id integer PRIMARY KEY, tenant text NOT NULL, evidence text NOT NULL);
INSERT INTO restore_acceptance_fixture VALUES (1,'tenant-alpha','owned fixture'),(2,'tenant-beta','separate fixture');
SQL
pg_dump -Fc --no-owner -d aegis -f "$backup"
createdb -T template0 aegis_restore_ci
pg_restore --exit-on-error --no-owner --no-acl -d aegis_restore_ci "$backup"
source_schema=$(pg_dump --schema-only --no-owner --no-acl -d aegis | sed '/^\\restrict /d;/^\\unrestrict /d')
restored_schema=$(pg_dump --schema-only --no-owner --no-acl -d aegis_restore_ci | sed '/^\\restrict /d;/^\\unrestrict /d')
[ "$source_schema" = "$restored_schema" ]
[ "$(psql -X -At -d aegis_restore_ci -c "SELECT string_agg(tenant || ':' || evidence, ',' ORDER BY id) FROM restore_acceptance_fixture")" = "tenant-alpha:owned fixture,tenant-beta:separate fixture" ]
[ "$(psql -X -At -d aegis_restore_ci -c 'SELECT version_num FROM alembic_version')" = "017_evidence_legal_holds" ]
echo 'PASS: disposable schema, migration revision and synthetic tenant records restored'
# Service containers are destroyed by CI; no live backup or production access used.
