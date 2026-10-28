# AEGIS — new recovery checkpoint after bceb282 (2026-10-28)

**Release decision: NOT PRODUCTION READY.** The shipped ZIP is the full recoverable source and Git history, not an accepted final public deployment. Exact exported commit and per-file hashes are in `RECOVERY_VERIFICATION.json`.

## Implemented in this checkpoint

1. Tightened both authorized discovery endpoints: on every request and before publishing the response, re-read the authorization, asset, user, org, mutable scan-pause state, and membership. A missing/revoked/expired/tampered grant, changed origin/org, inactive account, or changed role terminates discovery; one-use grants are revoked on completion/failure. No additional scan or remediation authorization is inferred.
2. OpenAPI 3 JSON preview now filters bounded, plain GET paths using a testable shared TypeScript helper. Sensitive endpoints, URL-encoded/templated/ambiguous paths, unresolved references, authenticated operations and operations with a request body are not imported. The customer still reviews candidates and separately consents; the server validates all requested paths.
3. Health-monitor cleanup tolerates an already-deleted monitor and missing prior authorization, without reviving removed rows. The scheduler continues attempting other due monitors after one broker dispatch fails; unsuccessful dispatches remain due for retry. This is not an exactly-once delivery guarantee.
4. Added regression tests for discovery grant drift, root and recursive endpoint lifecycle, monitor deletion/broker errors, and OpenAPI candidate handling. No live public website was probed.

## Actual verification on this checkout

| Test | Result | Evidence |
| --- | --- | --- |
| Standalone discovery grant Python unit cases | 3 passed | discovery-grants-unit.log |
| In-memory SQLite discovery endpoint lifecycle | 6 passed | discovery-lifecycle-unit.log |
| Standalone monitor cleanup and dispatch | 3 passed | health-safety-unit.log |
| Previously implemented discovery deadline regression | 4 passed | discovery-deadline-recheck.log |
| OpenAPI TypeScript helper standalone `tsc` | passed | openapi-helper-tsc.log (empty output means success) |
| Compiled OpenAPI helper Node assertions | 4 passed | openapi-helper-node.log |
| PHP plugin syntax and WordPress contract double | passed | wordpress-syntax-recheck.log and wordpress-contract-recheck.log |
| Disposable SQLite migrations head -> 013 -> head -> check | passed, 0/0/0/0 | sqlite-migrations-current.log |
| GitHub Actions YAML parse | passed | ci-config-check.log |
| Python bytecode compilation | passed | executed without generated log |

These groups are not replacements for full backend/frontend/browsers/WordPress/PostgreSQL acceptance. Additional Vitest file `apps/web/tests/openapi-candidates.test.ts` was added but was **not executed under Vitest** (node_modules absent). TypeScript application typecheck and Next production build were **not rerun**.

## External environment blockers and required gates

- Current container provides PHP, Python, FastAPI/SQLAlchemy/Alembic and global TypeScript, but no Celery or Redis Python dependency, no complete Next `node_modules`, and no PostgreSQL/Redis test servers. The runtime cannot resolve package registry hostnames. Therefore full `pytest`, Vitest, Playwright and real PostgreSQL/Redis worker verification cannot be claimed here.
- The actual WordPress core/CLI fixture is absent. The PHP contract is not a real WordPress activation/browser acceptance; use the existing CI `wordpress-runtime` job on an isolated MySQL/WordPress test instance.
- Run the complete backend suite on a frozen source tree, with the current Firebase public config (do not use a stale assertion collected during edits); test isolated PostgreSQL migrations 014–016, Celery/Redis/SMTP and all live-independent integrations; run frontend unit/build/Playwright journeys.
- Remaining feature completeness: official hosting-provider SmartVerify adapters, full staging/authorized AutoFix application and rollback, Launch Guard dependency/release gates, broad API and browser journeys, Vault retention/legal holds, specialized reports/admin review and cloud deployment acceptance. See the preexisting `PROJECT_STATUS.md` feature matrix. No production customers or unowned sites may be scanned or edited.
- **No production launch** until these gates pass and the user approves deployment. Payments, pricing and conversational assistant remain disabled. Security Scan authorization remains separate from AutoFix/edit authorization.

## Reproduce focused tests (offline, when source deps present)

```bash
PYTHONPATH=apps/api python tests/test_discovery_grants.py -v
PYTHONPATH=apps/api python tests/test_discovery_lifecycle_unit.py -v
PYTHONPATH=apps/api python tests/test_health_safety_unit.py -v
PYTHONPATH=apps/api python tests/test_discovery_deadline.py -v
php -l integrations/wordpress/aegis-verify/aegis-verify.php
php tests/wordpress_contract.php
tsc --noEmit --strict --target ES2022 --module ES2022 apps/web/lib/openapi-candidates.ts
```

For full suite and cloud paths, follow `CONTINUE_FROM_HERE.md`, `DEPLOYMENT_HANDOFF.md` and `.github/workflows/ci.yml`. Never point migration/integration tests at a production database.
