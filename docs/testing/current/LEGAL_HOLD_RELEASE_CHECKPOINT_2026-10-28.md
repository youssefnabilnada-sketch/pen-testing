# AEGIS continuation engineering checkpoint — evidence holds, release review, transport budgets

**Status: development, not production validated.** This checkpoint extends the previously transferred project and does not restart it.

## Implemented and preserved

1. Evidence Vault legal holds: immutable historical placement records and auditable releases, only for workspace owner/admin; reasons recorded; no deletion or automated expiry activated. Added report-list active-hold indicator, authorized history endpoint, customer controls, and PostgreSQL/SQLite Alembic migration `017_evidence_legal_holds`. PostgreSQL production migration is **not yet verified**.
2. Release Guard reviews: broader advisory-only classification of dependency manifests/lockfiles, CI workflows, deployment assets, security-boundary files and migrations. Manual reviews surfaced in UI. No audit, staging deployment, automated merge or compliance certification is implied.
3. Approved HTTP transport: all authorized GET requests use their approved timeout for socket/response watchdog (normal assessment 5s, discovery supports shorter approved budgets). This does not bound DNS lookups or prove external network reliability.
4. CI scope: PostgreSQL migration head/required-table assertions updated through 017; new opted-in isolated desktop/mobile Website Health browser job. Existing WordPress/MySQL, backend, frontend and PostgreSQL/Redis jobs retained. Added full API regression case to existing CRM/Vault integration suite.

## Verification completed in THIS environment

- `PYTHONPATH=apps/api python -m unittest -q tests.test_evidence_legal_holds_unit tests.test_launch_guard_review_unit tests.test_transport_timeout_unit tests.test_discovery_deadline tests.test_discovery_grants tests.test_discovery_lifecycle_unit tests.test_health_safety_unit tests.test_crawler_html_resilience` — **29 PASS**, no failures.
- SQLite disposable DB Alembic: `upgrade head` → revision `017_evidence_legal_holds` and table/columns checked; `check` clean; `downgrade 016_crm_vault` removed hold table; `upgrade head` and `check` clean. See `legal-hold-migration-sqlite.log`. **NOT PostgreSQL acceptance.**
- Modified `VaultPanel.tsx`, `LaunchPanel.tsx`, `page.tsx` transpile syntax checks passed using globally available TypeScript. **NOT full Next.js build or TypeScript typecheck.**
- PHP contract tests and plugin `php -l` passed; **NOT real WordPress runtime acceptance.**
- Python `compileall` and GitHub Actions YAML parsing passed.

## Blocked, not silently passed

The environment cannot install the project's pinned dependencies (`Celery` missing; package download rejected) or install full Next.js node_modules. Full pytest fails while importing `celery` before collecting tests. PostgreSQL and Redis services and an installed WordPress runtime are also unavailable here. CI definitions are authored, **not run** in this container. No live Firebase, SMTP, GitHub provider, customer asset, or deployed cloud acceptance took place. Historical full Backend 292 passed/6 skipped/1 failed and Frontend 77 passed are **not current frozen-tree verification**.

## Must be done before any public launch

- Run isolated PostgreSQL migrations through 017 and backup/restore; complete backend 85% coverage gate, full Next/Vitest/build, CI and browser acceptance on both desktop/mobile; resolve failures.
- Fix real WordPress bootstrap, verify the plugin in a complete disposable WordPress runtime and finish SmartVerify provider adapters with secure permissions and controlled fixture tests.
- Complete authorized AutoFix staging identity/rollback, full Scan→AutoFix→approved retest UI journey, Launch Guard staging/dependency evidence (not just risk flags), API assessment, tenant isolation, sensitive-action MFA, admin and missing specialist reports.
- Test service-separated FastAPI, workers/beat, PostgreSQL, Redis, Firebase live auth and trusted SMTP/domain in production-like cloud; backups, telemetry, privacy/security and operational readiness. Public deployment requires explicit user-owned accounts and approved credentials; never upload secrets.

Keep `PAYMENTS_ENABLED=false`, `PRICING_ENABLED=false`, `BILLING_MODE=disabled`, conversational assistant off; customer-owned site verification, scanning, editing, and retesting require independent scoped approvals. No automated live customer scans or production changes.
