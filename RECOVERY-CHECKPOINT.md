# Recovery checkpoint — 2026-10-27

User direction: stabilize version 0.1 first; additional expansion belongs to 0.2. Live GitHub verification is not a release blocker at the user's request. Payments remain disabled. Saving is a recovery operation, not a final handover.

Observed: workspace returned to commit b929576; recent uncommitted discovery/health/Launch Guard/native-smoke files and logs were absent; prior running process ID was unknown. The cause is not established. Latest persistent archive version 26 was recovered into the existing repository and committed as c4bd6b6. It contains the guarded PostgreSQL/Redis CI harness and recurring explicit-path API, but not the subsequently described additions. Do not use those lost-source test runs as acceptance evidence for this recovered tree.

Next concrete tasks:
1. Restore explicit recurring-path UI, bounded root-link discovery and owned-fixture tests; commit and persist each verified change.
2. Restore native process smoke runner and execute against Next/FastAPI/Redis/Celery/SMTP with an explicitly documented temporary SQLite limitation.
3. Restore sampled health views and advisory release reviews only if they can be verified without delaying core 0.1 stability; otherwise classify them as 0.2.
4. Re-run current-tree backend, frontend, migrations and build; record exact logs and measured coverage.
5. Verify live Firebase access if authenticated service access becomes available. Existing public project configuration is not by itself a successful server-side login test.
6. PostgreSQL integrated runtime and browser acceptance remain unverified. Do not declare production readiness.

## Durable continuation
Restored and committed recurring path UI, bounded authorized root discovery API/UI and deterministic tests. Recovered current-tree evidence: recovered-core.log 11 passed; recovered-discovery.log 33 passed; recovered-web-final.log contains frontend/typecheck results. Native multi-process runtime test restored in tests/test_native_runtime.py, invoked with AEGIS_NATIVE_SMOKE=1 through scripts/test-with-redis.py. Production frontend rebuild is in progress; do not mark its outcome until the process exits. Next: finish build, run native smoke with isolated Redis, record and persist actual evidence. Health/Launch Guard additions from lost uncommitted state are NOT in this recovered tree and must not be advertised as delivered.

Verified on the recovered source: 59 frontend tests passed; TypeScript and production build passed; opt-in native frontend/API/Redis/Celery/SMTP integration passed together with the owned-target journey and Redis checks (3 passed, recovered-native-runtime.log). Temporary SQLite was used; no PostgreSQL, browser or live-provider claim. Full backend coverage run remains in progress in recovered-regression.log. Payment processing remains disabled.

Current regression completed: 236 passed, 2 opt-in integration tests skipped in default run; separate native Redis runner passed 3 selected tests. Backend statement coverage 91.95%. Verification report: docs/testing/VERIFIED-0.1-RECOVERY.md. Firebase CLI version 15.34.1 installed and login flow initiated, but no completed authenticated session or live project operation has been verified. Do not store login URLs, authorization codes or credentials in this archive. Next step is authenticated Firebase validation and a capable PostgreSQL/browser acceptance environment. GitHub is not a blocker under the latest user instruction.

Final saved continuation: Firebase account/project access is now VERIFIED; project ACTIVE and live SDK configuration fetched/matched. Do not repeat the old claim that Firebase access is absent. Application/backend Firebase sign-in remains unverified. No credentials or login codes are stored in source. Real owned-target discovery suite passed 10 tests. User requested delivery before credits expire; all current source and evidence must be preserved. Next: verified server runtime/credentials and browser acceptance; optional expansion remains 0.2.
