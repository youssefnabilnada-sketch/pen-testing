# AEGIS — Intelligence history and PDF evidence development checkpoint

**Release state: DEVELOPMENT. Public production release is NOT APPROVED.**

## Completed implementation

- Added a tenant-scoped compatibility layer for old/deleted/mismatched inventory, advisory-impact, schedule and retest references. Missing or cross-organization associations are never displayed as verified inventory, current advisory matches, or valid recurring assessment consent.
- A revoked, expired, non-recurring, cross-asset or missing authorization is displayed as `blocked_no_current_consent`; the stored schedule can still be disabled. Missing baseline authorizations no longer cause the retest history endpoint to fail or reveal another asset's approved paths.
- Stale/missing historical authorizations no longer prevent an owner from disabling an existing schedule; previously saved invalid report comparisons are normalized to an empty object for display.
- Added an access-checked, organization-scoped Intelligence evidence PDF with bounded inventory and advisory matches, escaped customer-supplied text, explicit sampling limits, and NO claim of verified exploitability/security certification. Added its link in the customer Intelligence panel.
- Historical remediation retest projections now hide jobs/reports across organization boundaries and do not display invalid baseline path associations.

## Verified in this environment

- `PYTHONPATH=apps/api python -m unittest discover -s tests -p 'test_*unit.py' -q`: **75 passed** (14 new unit methods; includes 10 history and 4 PDF checks; overlaps with earlier 61-test total).
- Python `compileall`, `git diff --check`: passed.
- TypeScript TSX parser/transpilation syntax of modified Intelligence panel: passed, NOT full typecheck or production build.
- Isolated PHP WordPress contract: passed; NOT full WordPress runtime.

## Blocked/unverified for public release

- The full FastAPI/Pytest suite in this environment cannot collect without Celery and related dependencies. Current frontend dependencies and PostgreSQL/Redis service instances are not installed. No recent integrated browser, full npm test/build, live WordPress, live Cloudflare, genuine SMTP/Firebase or cloud staging checks have passed on this commit.
- Core unfinished requirements remain official hosting-provider integrations, WordPress runtime acceptance, broader AutoFix staging/rollback identity, live GitHub/Launch Guard approval flow, full browser acceptance, operational backups and cloud deployment.
- Previously successful backend/frontend tests are historical, NOT acceptance evidence for this modified tree. Run all required CI jobs on isolated infrastructure, correct failures, then execute live staging acceptance and security review before public launch.

## Operating constraints

Payments, pricing, billing and the conversational AI assistant remain disabled. Safe scan consent and AutoFix permission remain independent; do not scan outside verified, explicitly authorized scope. No live sites were assessed. No credentials or private tokens should be included in the archive.
