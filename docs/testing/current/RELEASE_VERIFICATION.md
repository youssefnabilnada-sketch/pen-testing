# AEGIS — current-turn verification and release limitations

This is a **new, unfinished development checkpoint**, not a production release.
Source restored from the submitted Git bundle at `21ca70a` and compared byte-for-byte with the uploaded ZIP's project tree.

## Code changes
- Recursive discovery now caps each network request's socket/HTTP timeout by the time remaining in the user-authorized crawl window, bounds inter-request sleep, and refuses new candidates when the elapsed crawl budget expires. A `timed_out` flag distinguishes time-budget exhaustion.
- Ordinary security assessment timeout remains fixed at five seconds; only separately authorized passive link discovery may use a smaller positive timeout.
- Added four dependency-light unit tests for deadline behavior, scope isolation, safe truncation, and pinned transport timeout.
- Added a disposable-database CI verification for PostgreSQL migration revisions 014–016 (downgrade and re-upgrade, table and Alembic head assertions). It has **not** been executed against PostgreSQL here.

## Tests actually executed in this environment
- Four discovery deadline unit tests: **4 passed**, via `PYTHONPATH=apps/api python tests/test_discovery_deadline.py -v`.
- WordPress plugin PHP syntax: **passed**, via `php -l integrations/wordpress/aegis-verify/aegis-verify.php`.
- PHP contract tests: **passed**, via `php tests/wordpress_contract.php`. This is **not a WordPress runtime** test.
- Controlled synthetic three-page crawler demonstration: **passed** using explicit in-memory authorized fixture; no public website assessed.
- Disposable SQLite migrations upgraded through revision `016_crm_vault`, downgraded to `013_agency`, upgraded again, and `alembic check` showed no pending operations. **SQLite is not PostgreSQL proof.**
- Python `compileall` for the API: **passed**.
- GitHub Actions YAML parsed with PyYAML: **passed**.

## Blockers and missing acceptance
- Full backend tests **not executed**. Test collection failed because `celery` is not installed. Installing pinned Python dependencies failed due unavailable DNS/network in this runtime. See `backend-baseline-blocked.log` and `dependency-install-network-blocked.log`.
- Full frontend, TypeScript, build and Playwright/browser tests **not executed**. `node_modules` was intentionally excluded from the transfer; no online dependency installation is available.
- PostgreSQL, Redis, cloud workers and Firebase live provider tests **not executed** in this environment. Only the isolated SQLite migration smoke test passed.
- Full WordPress bootstrap and runtime acceptance **not executed**. PHP is present, but an actual isolated WordPress fixture is not available.
- Cloud deployment is **not configured or validated**. Requires hosting, managed services, authentication secrets, owned test assets, production email sender, and a user-approved deployment.
- All remaining workstreams and the detailed module status remain documented in `PROJECT_STATUS.md`. Do not claim the code is production-ready.

## Release decision
**NOT READY FOR PUBLIC LAUNCH.** This archive is an updated, recoverable source checkpoint with the improvements above. Continue from this exact Git commit after installing dependencies in an authorized testing environment, then run the full test suite and cloud release gates.

## Additional hardening in this development checkpoint
- Production startup now rejects web origins with credentials, query strings, fragments or nonstandard ports; invalid Redis URLs; additional billing flags; test-mode aliases; missing public Firebase identity configuration; unencrypted/unconfigured SMTP; and missing/malformed MFA secret. This is a configuration gate, not proof that cloud services are running.
- A dependency-light isolated configuration check exercised **19 cases successfully**. The standard `tests/test_production_runtime.py` suite was expanded but cannot be collected here because `celery` is absent from this runtime.
- Health worker authorization handling now stops safely if a monitor, authorization, asset, or user record disappears during sampling. The full worker integration tests remain unexecuted in this environment.
- Added an optional CI job to install an isolated official WordPress fixture and execute `tests/wordpress_runtime.php` against it. YAML parsing, PHP syntax and the PHP contract test passed locally; the **new WordPress CI job has not run yet**, and its actual runtime result remains unknown.
- No frontend, backend aggregate, PostgreSQL, Redis, cloud deployment, or external GitHub provider acceptance tests were completed in this environment. The original release decision remains **NOT READY FOR PUBLIC LAUNCH**.
