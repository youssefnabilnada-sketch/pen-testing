# AEGIS continuation checkpoint — OpenAPI preview and safe discovery

**Status: DEVELOPMENT CHECKPOINT ONLY; NOT PRODUCTION READY.**

## Changes implemented after 7ff90fe

- The OpenAPI import preview now checks explicit top-level `servers` against the selected verified origin; documents with mismatched hosts, server variables, ambiguous multi-server declarations, base paths or query/fragment overrides fail closed. Path/operation-level server overrides are not imported.
- Endpoint previews reject required or unresolved OpenAPI parameters, any headers/cookies and ambiguous parameter structures. Only bounded, plain GET candidates are presented, and the customer must separately authorize any assessment.
- Editing the OpenAPI source, changing the selected origin, starting an import, or encountering an import error clears the prior consent/notification state in the UI. This is a UI guard, not a substitute for server-side authorization.
- The crawler rejects additional sensitive compound path segments (e.g. `/api/logout-v2`, `/account_disable`, `/billing.refund`) and tolerates `<link rel>` without a value and mixed-case canonical metadata. Requests remain explicitly scoped and bounded.
- Added `tests/test_crawler_html_resilience.py` and expanded `apps/web/tests/openapi-candidates.test.ts`.

## Tests performed in this container (not historical)

- `PYTHONPATH=apps/api python -m unittest -v tests.test_discovery_deadline tests.test_discovery_grants tests.test_discovery_lifecycle_unit tests.test_health_safety_unit tests.test_crawler_html_resilience`: **20 passed**.
- `tsc --noEmit --strict --target ES2022 --module ES2022 apps/web/lib/openapi-candidates.ts`: **passed**.
- Compiled the standalone OpenAPI TypeScript helper with `tsc` and checked 10 accept/reject scenarios using Node.js assertions: **10 passed**.
- `php -l integrations/wordpress/aegis-verify/aegis-verify.php`: **passed**.
- `php tests/wordpress_contract.php`: **passed** (mocked WordPress contract only).
- `python -m compileall -q apps/api/aegis/crawler.py tests/test_crawler_html_resilience.py`: **passed**.

No full backend pytest, Next.js build, Vitest, Playwright, real WordPress runtime, PostgreSQL/Redis tests, live Firebase/SMTP, or deployed customer journeys were run for this checkpoint. Vitest file is authored but not executed. Python Celery and full Node dependencies are unavailable in the current container; package-registry access was previously blocked. Results above must not be presented as complete application acceptance.

## Remaining release gates and incomplete features

1. Complete backend regressions on the frozen source; run PostgreSQL migrations 014-016, isolated Redis/Celery/email integration and DB backup/restore.
2. Correct isolated WordPress bootstrap failure and execute full plugin acceptance. Implement and test optional, scope-limited SmartVerify provider integrations where supported.
3. Finish staging/approval/restore/rollback workflows for AutoFix; no autonomous production deployment. Test end-to-end Scan -> authorized AutoFix -> retest.
4. Complete Launch Guard dependency/staging gates, Agency/CRM/Vault retention/administration, API assessment, reports and accessible browser journeys.
5. Run full Next/Vitest/build/Playwright desktop and mobile, and final security/privacy/tenant isolation tests. Perform cloud production-like verification of frontend, API, worker/scheduler, PostgreSQL, Redis, Firebase and email.

Keep PAYMENTS_ENABLED/PRICING_ENABLED=false; conversational assistant off; Scan/AutoFix separately authorized. Do not scan or modify third-party assets without verifiable ownership and scoped consent.
