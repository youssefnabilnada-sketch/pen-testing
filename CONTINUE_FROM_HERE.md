# Latest recovery and remediation UX checkpoint

Read `docs/testing/ux-redesign/RESUME.md` first. Continued exact remote bd3d0e1 on the same feature branch; baseline CI all 10 jobs passed. Retest stale-response protection, comparison states and additional Arabic guidance implemented and locally tested. Candidate CI must be checked. Full redesign remains incomplete; production untouched.

# Experience continuation — 2026-10-30

Read `docs/testing/ux-redesign/EXPERIENCE.md` for current implementation and verification. Same `feature/aegis-ultimate-ux-redesign` branch; shared glass surfaces, progressive evidence/FastFix details, partial Arabic/RTL and offscreen 3D optimization added. 93 frontend tests passed. Browser CI pending; complete redesign still unfinished. Production untouched.

# Current UX development checkpoint — 2026-10-30

Continue on `feature/aegis-ultimate-ux-redesign`, from the preserved audit branch. Read `docs/testing/ux-redesign/STATUS.md` for exact scope, tests, browser blocker and next steps. UX navigation/onboarding/verification improvements are implemented; the complete redesign is NOT finished. Production services untouched. Earlier entries below are historical.

# Verified preservation checkpoint — 2026-10-30

Repository: https://github.com/youssefnabilnada-sketch/pen-testing
Branch: `audit/fastfix-guidance-20261028`. Latest verified implementation:
`cef9915b3100e7acedd403e28d893373555d8400`. This documentation-only checkpoint
descends from it. Do not overwrite with earlier recovery snapshots or merge unfinished work into main.

## Preserved and verified
The complete current branch was cloned with its 22 existing commits, including
WordPress SmartVerify, notification changes, migrations and all previously committed source.
FastFix includes strict JSON duplicate/nonfinite/precision rejection, UTF-8 and generated-output
size limits, evidence-bound guidance and developer handoff, plus reviewed Vercel and
Netlify static nosniff adapters with backup/restore rehearsal and existing approval/MFA gates.
No implementation was changed by this preservation operation.

GitHub Actions run 40841851000 on the implementation commit was independently checked:
10/10 jobs succeeded: backend, web, PostgreSQL migrations, integrated PostgreSQL/Redis,
native runtime, WordPress runtime, browser smoke, browser health, public-repository-history,
and predeploy-ci-evidence. Run 40841846973 also reports success.
https://github.com/youssefnabilnada-sketch/pen-testing/actions/runs/40841851000

Historical focused results preserved in docs/testing/fastfix-audit/OCT29_VALIDATION.md:
43 repository/Netlify/recovery/configuration tests; 34 guidance tests; 7 frontend tests;
TypeScript and Ruff passed. Earlier 22/32/2 counts describe the prior increment.
No tests were rerun during this save-only operation. No current failing CI job was observed.
Full test counts/coverage were not extracted from latest CI logs: do not substitute
historical coverage or the earlier 75-frontend claim for a measurement of this commit.

## Incomplete / release gates
NOT production-ready. Universal FastFix is incomplete. Netlify functions/SSR/proxy responses,
competing header configurations and deployed revision are not verified. Remaining:
authorized static staging acceptance; additional adapters and exact-change approvals;
authenticated full customer journeys; real Firebase/email/cloud/recovery acceptance;
remaining platform/privacy audit and AI Agent quality evaluations.
Public AI Assistant and payments/pricing remain disabled; no live site was modified.
See OCT29_VALIDATION.md and the preserved historical module descriptions below.
Successful CI does not establish production acceptance.

## Exact continuation
1. Clone with authorized GitHub access:
   git clone --branch audit/fastfix-guidance-20261028 https://github.com/youssefnabilnada-sketch/pen-testing.git
2. Run git status --short and git log -3 --oneline. Confirm the implementation SHA above is an ancestor.
3. Read this section and docs/testing/fastfix-audit/OCT29_VALIDATION.md first.
   Earlier status sections are historical, not evidence that latest CI remains blocked.
4. Next implementation priority: owned Netlify static staging fixture, competing header
   policy checks and deployed-revision evidence. Then resume additional adapter/approval work.
   Reuse unchanged passing tests; run targeted tests for changes and full CI before release.
5. Obtain authorized provider/staging access securely when needed. Never put credentials in Git.
   Keep payments and public AI disabled. Do not deploy or merge based on this checkpoint.
6. ZIP restores source; included Git bundle restores this branch's full reachable history:
   git clone AEGIS_SECURITY_CLOUD_HISTORY.bundle aegis-restored
   The bundle does not include unrelated remote branches.

---
 
# Current audit/FastFix checkpoint

Continue from the latest audit branch and docs/testing/fastfix-audit/STATUS.md. Only FastFix may receive major expansion; elsewhere fix reproduced defects only. New config parser regression fix and evidence-bound guided remediation UI/API are focused-tested. Universal FastFix and the whole-platform audit are NOT complete. Candidate CI must be reviewed. Older continuation scopes below are historical and superseded where conflicting.

# Latest engineering checkpoint — 2026-10-28 (SmartVerify/AutoFix/CI)

**This is NOT a public-release-ready build.** Staging AutoFix evidence now requires exact observed paths and rejects contradictory detector records. The CI release gate requires eight jobs, including fresh separate-process services and desktop/mobile Chromium smoke. A read-only staged HTTPS probe was added but NOT run against live infrastructure. **84 isolated Python unit tests passed**, along with PHP contract, SQLite migration round-trip through 017 and CI YAML structure. Full pytest collection remains blocked by missing Celery, and PostgreSQL/Redis/Next dependencies/WordPress runtime are unavailable here. See `docs/testing/current/SMARTVERIFY_AUTOFIX_CLOUD_VALIDATION_2026-10-28.md`. No real hosting, WordPress or provider deployment has been certified.

## Latest checkpoint — Intelligence history, PDF, and missing-reference safety (2026-10-28)

Continue from latest Git HEAD; no rebuilding. Tenant-scoped historical data projections and a limited intelligence PDF report are implemented, with 75 standalone Python unit tests passing. The new route is `/organizations/{org_id}/intelligence/report.pdf`. This export is **not** a public release. Re-run the full integrated CI against the frozen source, especially browser Intelligence report download and PostgreSQL/Redis/WordPress acceptance. See `docs/testing/current/INTELLIGENCE_RELEASE_HARDENING_2026-10-28.md`.

---

# Resume newest AEGIS code — 2026-10-28

Continue from this repository's Git HEAD, not from the older 580/622/627-file transfers. Preserve all previous source, milestones and history. Recent changes: history lists fail safely on deleted/mismatched assets or authorization, staging evidence is tenant-bounded and fail-closed, and predeploy CI requires all six test jobs. See `docs/testing/current/RELEASE_CONTINUATION_2026-10-28.md`. **The source is NOT public-production-ready.** Run the GitHub Actions CI jobs in a private repository and complete live cloud checks; no real customer targets. No credentials in Git. Preserve payments/pricing/AI chat disabled.

---

# Resume newest source — Website Health PDF

Continue from latest commit, not older transfer snapshots. Tenant-scoped health-observation PDFs and customer links now exist; independent report tests passed. Re-run full API permission integration and full browser journeys when dependencies are provisioned. The HTTP API tests added to `tests/test_health_monitoring.py` have NOT run in this container. For boundaries and remaining launch gates see `docs/testing/current/HEALTH_REPORT_2026-10-28.md`.

---

# Continue from latest Launch Guard / Cloudflare code checkpoint

Source extends previous `2a9875b`. Completed a tenant-scoped advisory Launch Guard PDF and streaming Cloudflare API hardening. 51 isolated Python tests passed; complete acceptance not executed. Run GitHub Actions and PostgreSQL/WordPress/Next/Playwright in proper isolated environment before production; then complete the remaining modules. Do not expose a public site or call this final until the gates in `docs/testing/current/LAUNCH_REPORT_AND_CLOUDFLARE_2026-10-28.md` pass. Payments and assistant remain disabled; authorization boundaries unchanged.

---

# Latest source continuation — Cloudflare response hardening

Continue from the latest Git commit and archived source (not older `2a9875b`). Implemented bounded Cloudflare response streaming, IDNA canonicalization, malformed record rejection and permission rechecks; 47 isolated Python tests passed plus PHP WordPress contract. Before claiming release readiness run integrated CI tests including WordPress, PostgreSQL migrations 014–017 and complete browser + deployment acceptance. Never call standalone contract tests full acceptance. Details: `docs/testing/current/CLOUDFLARE_RESPONSE_HARDENING_2026-10-28.md`.

---

# Latest continuation instructions — 2026-10-28 Cloudflare checkpoint

Continue from the newest committed source, not the original 555/580-file transfer. New Cloudflare SmartVerify preview/publish endpoints and a customer opt-in UI are implemented; NEVER treat creation of a DNS proof as authorization to scan or edit. Provider tests: 12 passed; combined isolated suites: 41 passed. API/JS integration tests exist but could not run here (Celery and node_modules unavailable); see `docs/testing/current/CLOUDFLARE_SMARTVERIFY_CHECKPOINT_2026-10-28.md`. First run new API and UI integration tests with dependencies installed, verify an owned disposable Cloudflare zone, and run full PostgreSQL+Redis+WordPress+browser CI; then remaining modules and production cloud acceptance. Secrets are never in source. No public launch claim.

# Newest verified continuation — 2026-10-28

1. Restore **latest** source ZIP and embedded/standalone Git bundle; its `RECOVERY_VERIFICATION.json` is authoritative. Do not overwrite with older checkpoint.
2. Read `docs/testing/current/LEGAL_HOLD_RELEASE_CHECKPOINT_2026-10-28.md`, then this file and current `PROJECT_STATUS.md`/`TEST_RESULTS.md`. Legal holds + migration `017_evidence_legal_holds`, Launch Guard risk classification, approved transport timeouts and browser-health CI were added after `2a118fa`. Do not rebuild them.
3. First use a secure CI/Linux environment with Python 3.12+ and pinned dependencies, Node 22/npm, isolated PostgreSQL+Redis, PHP/WordPress and headless browser. Run full Backend pytest with 85% coverage gate, full Next/Vitest/build, isolated PostgreSQL migration upgrade/downgrade through 017, WordPress runtime, and browser CI; fix any failures. Never use customer data.
4. Then complete remaining SmartVerify provider adapters, AutoFix staging identity/rollback, missing specialist reports and browser workflows, and cloud production-like verification. Do not enable payments/pricing or untested AI assistant; keep Scan/AutoFix separately authorized.
5. Commit validated changes and re-export with `python scripts/export-recovery.py /absolute/output` on a clean worktree. The previous original test logs are historical; do not label them as current release verification.

**Current continuation checkpoint (2026-10-28):** New bounded OpenAPI preview (verified origin, parameters, overrides), compound-sensitive-path filtering and malformed HTML resilience. 20 focused Python tests, 10 standalone Node assertions, standalone TypeScript check and PHP WordPress contract passed. Not a complete backend/frontend/cloud acceptance. Details: `docs/testing/current/OPENAPI_CRAWLER_CHECKPOINT_2026-10-28.md`.

---

# Newest 2026-10-28 coding checkpoint (supersedes older session notes)

Continue from the current ZIP's `RECOVERY_VERIFICATION.json` and embedded matching Git bundle, **not** from the older bceb282 export. The new checkpoint strengthens authorization lifetime in both discovery endpoints; adds testable OpenAPI GET import filtering; makes health worker cleanup safe for missing monitors and scheduler dispatch tolerant of a single broker failure. Exact implementation and offline evidence: `docs/testing/current/DEVELOPMENT_CHECKPOINT_2026-10-28.md`. These improvements **do not close** the original production acceptance or feature matrix. Avoid reimplementing these changes. Full backend/frontend, PostgreSQL, real WordPress and cloud/browser gates remain unverified in this environment. Preserve all earlier features and keep payment/pricing, conversational AI disabled. Do not expose live customers to unfinished scanning or editing.

---

# Newest checkpoint instructions — 2026-10-28

Continue from the newest Git commit and `RECOVERY_VERIFICATION.json` in the new archive, not the old transfer metadata. The production runtime now validates stricter public origin/Redis/Firebase/SMTP/MFA and billing-disabled settings; supply actual production secrets privately through the host. The health monitoring worker safely handles disappearing records. `.github/workflows/ci.yml` now has an **untested** isolated WordPress runtime acceptance job. On an authorized CI runner with dependencies, prioritize: run full backend regression, the PostgreSQL 014–016 job, the WordPress runtime job, current frontend+browser tests, and resolve any failures. Then continue implementation gaps; see `PROJECT_STATUS.md` and `docs/testing/current/RELEASE_VERIFICATION.md`. Do NOT publicly deploy based on this archive alone.

---

# Latest current-turn engineering checkpoint — 2026-10-28

Updated from the user's uploaded source and verified Git bundle. Implemented a tighter authorized recursive-discovery time budget and added regression tests. Added PostgreSQL 014–016 CI round-trip checks (not yet run on PostgreSQL). Four standalone discovery unit tests, WordPress PHP contract, and disposable SQLite migration round-trip passed. Full backend tests could not collect (missing Celery); installing dependencies failed due no network. No full frontend/browser/live cloud or real WordPress runtime acceptance. **This is NOT a final or public-production-ready release.** See `docs/testing/current/RELEASE_VERIFICATION.md` for exact results. Continue from the latest Git commit; preserve all prior features, payments/pricing OFF, AI Assistant OFF, and Scan/AutoFix separation.

---

# Resume the latest transferred source

1. Extract AEGIS_SECURITY_CLOUD_LATEST_TRANSFER.zip into a new directory. Source root is AEGIS-Security-Cloud. Do not restore the older workspace.
2. Restore Git history: `git clone AEGIS_SECURITY_CLOUD_TRANSFER_HISTORY.bundle aegis`. The bundle is supplied separately and embedded in the ZIP. Its tip source matches the ZIP source. Do not overlay old checkpoints.
3. Read the leading current section of PROJECT_STATUS.md and TEST_RESULTS.md. Original HANDOFF_METADATA.json/SOURCE-MANIFEST.json are retained historical transfer metadata. RECOVERY_VERIFICATION.json at archive root identifies THIS export.
4. Reinstall dependencies only: Python3.12+, `python -m pip install -r apps/api/requirements-dev.txt -r apps/api/requirements-firebase.txt`; Node22+, `npm ci` in apps/web. Runtime dependencies and credentials are excluded.
5. FIRST: freeze source/config and run `PYTHONPATH=apps/api python -m pytest tests --cov=aegis --cov-fail-under=85 -q` on isolated test storage. Windows PowerShell: set `$env:PYTHONPATH='apps/api'` before `python -m pytest ...`. The latest full run had a stale Firebase empty-key assertion collected during a config edit; final config/identity focused14 tests passed. Never mutate source while this validation runs.
6. Then use isolated PostgreSQL database exactly aegis_ci; tests drop schema, so NEVER use production data. Verify migrations014–016 and backup/restore; prior PostgreSQL proof only through013.
7. Recreate isolated PHP/WordPress runtime and debug tests/wordpress_runtime.php bootstrap. No new runtime success in this session.
8. Complete browser/module acceptance per PROJECT_STATUS matrix. Preserve payments/pricing OFF and AI assistant OFF. GitHub/Vercel publishing is the user's later task.
9. Public Firebase config is intentionally present by latest user instruction. Supply Admin credentials only via secure server configuration, not source or conversation. Still need cloud API/workers/scheduler/PostgreSQL/Redis, SMTP and Firebase providers/domains.
10. Save meaningful commits and use scripts/export-recovery.py after committing. Latest bundle/ZIP byte verification is recorded at archive root. Download/upload these actual files to the other account; chat history and temporary workspace do not transfer automatically.

# Current continuation — 2026-10-28

The newest source includes email crash recovery, CRM contact-consent withdrawal, Launch Guard provider/role validation, and the public Firebase configuration restored at the user's explicit request. Firebase web API keys in public config are intentional; no service-account private key is included. Prior sanitized-history statements describe the original transfer only.

Focused evidence: email recovery4 passed/1 Mailpit skipped; real loopback SMTP extension5 passed/1 Mailpit skipped; CRM backend3 and UI2 passed; Launch/repository23 passed; Firebase config/identity14 passed. Frontend77 passed; TypeScript and Ruff passed. Next build exited0 and produced BUILD_ID and production manifests. First full regression:291 passed,6 skipped,1 failed because its old test expected a removed Firebase key. Corrected test passed, then user requested restoration of that key. A second full run was already in flight during this config update: any config assertion from its collected older test is not evidence of the final file. Use firebase-restored-config.log (14 passed) for this change; final aggregate evidence must be explicitly recorded after completion.

No production deployment. PostgreSQL014–016, WordPress bootstrap and broader browser/module acceptance remain pending. Current runtime has no PostgreSQL/PHP executable. Earlier transferred Windows results remain historical. Payments/pricing and conversational AI remain disabled.

# Resume this actual source — do not rebuild

Extract the ZIP; project root is AEGIS-Security-Cloud/. Upload it to the other account; local files do not transfer automatically. Read PROJECT_STATUS.md, TEST_RESULTS.md and docs/requirements/MASTER-2026-10-26.md. Handoff/recovery requests are preserved under docs/requirements/.

## Repository and exact checkpoint
Original: C:/Users/asus/Documents/Codex/2026-10-28/files-mentioned-by-the-user-aegis/work/aegis. Branch master; implementation checkpoint before export b3face2. Exact final original commit and sanitized-history commit are in HANDOFF_METADATA.json. Restore history with `git clone /path/to/AEGIS_SECURITY_CLOUD_TRANSFER_HISTORY.bundle aegis-history`. The bundle is self-contained. Supplied public Firebase API-key values were removed from every exported revision; commit IDs differ but chronology/messages/implementation are preserved. Included source matches the restored bundle tip. Modified generated test PDFs were committed; no uncommitted changes intentionally omitted.

## Latest completed / incomplete work
Completed: CRM/Vault/Trust Center and focused checks; previously running full backend finished281 passed,6 skipped. Latest incomplete operation: WordPress download now succeeded, but tests/wordpress_runtime.php failed during actual WordPress bootstrap with a generic critical-error page; runtime acceptance is NOT passing. Export was prioritized; do not resume feature work until the user requests it in the destination account.

## Architecture and paths
apps/web: Next.js/React console, components, tests and e2e. apps/api/aegis: FastAPI/SQLAlchemy/Celery modules. apps/api/migrations:001–016_crm_vault. infrastructure: fixtures/emulator/deployment. integrations/wordpress: actual plugin. tests: backend/controlled integrations. docs/testing/oct28: latest logs and ENGINEERING_CHECKPOINT_HISTORY.md. docker-compose*.yml and .github/workflows/ci.yml preserve local/CI setup.
Frontend proxies /api to API_INTERNAL_URL. PostgreSQL stores state; Redis brokers default assessment/health/email tasks and an intelligence queue. One Celery beat scheduler is required. Production runs independently in cloud services.

## Recreate dependencies only, not project code
Use Python3.12, Node22+ and npm. Dependencies/runtime data are intentionally excluded.
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps/api/requirements-dev.txt -r apps/api/requirements-firebase.txt
$env:PYTHONPATH='apps/api'
.\.venv\Scripts\python.exe -m alembic -c apps/api/alembic.ini upgrade head
```
Run `npm ci` in apps/web using package-lock.json. Stale historical pnpm-lock.yaml is excluded from the ZIP; do not switch managers. Configure services first using DEPLOYMENT_HANDOFF.md. Secrets are not supplied.

## Test commands and precautions
Tests drop/recreate schema. NEVER point at customer data. PostgreSQL integration requires loopback and database exactly aegis_ci.
```powershell
$env:PYTHONPATH='apps/api'
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp=./work/pytest-new
.\.venv\Scripts\python.exe -m ruff check apps/api tests
```
From apps/web: `node node_modules/vitest/vitest.mjs run --configLoader native` (Windows loader workaround), `npm run typecheck`, `npm run build`. Browser: `npx playwright test` with E2E_BASE_URL and optionally E2E_CHROME_PATH. Install browser runtime if absent.
Opt-ins: AEGIS_ISOLATED_TEST_DATABASE_URL, AEGIS_TEST_BROKER_URL, AEGIS_TEST_REDIS_URL, AEGIS_TEST_MAILPIT=1, AEGIS_TEST_FIREBASE_EMULATOR=1, AEGIS_NATIVE_SMOKE=1, AEGIS_HEALTH_BROWSER=1. Firebase e2e uses E2E_FIREBASE_EMULATOR=1; health harness sets E2E_HEALTH=1. Native browser harnesses reserve8000/3001. Prior ports: PostgreSQL55432, Redis56379, Mailpit1025/8025, Firebase9099.
Original machine tools were sibling work/venv, work/php-runtime, work/postgres-runtime, work/redis-runtime, work/mailpit-runtime, work/firebase-tools. These and synthetic database directories are not exported. Reinstall on another machine.
Health tests replace DNS pinning ONLY inside their owned local fixture and dispatch scheduler jobs in-process. AutoFix tests create temporary controlled Git repositories/HTTP servers. GitHub tests use controlled API responses, not live repositories.

## Exact next implementation order after transfer
1. Ruff passed and full frontend passed75 tests across26 files. Do not repeat these solely for context. Diagnose tests/wordpress_runtime.php bootstrap failure using docs/testing/oct28/wordpress-runtime-test.log; then run affected checks. Current production build/browser acceptance remains outstanding.
2. Migrate/check014–016 on a NEW isolated PostgreSQL DB and verify DB backup/restore. PostgreSQL migration proof only through013; latest SQLite roundtrip through016 passed.
3. Full WordPress runtime acceptance; preserve contract tests. Implement scoped official hosting-provider adapters with secure credentials and controlled tests. No one-click provider implementation currently exists.
4. launch_guard.py/agency.py and console panels: complete dependency/staging evidence and browser flows. Strengthen provider response/head validation.
5. api_assessment.py/ApiAssessmentPanel.tsx: real local API/browser journey and OpenAPI import tests. email_alerts.py/NotificationPreferences.tsx/EmailHistory.tsx: UI/browser, crash/retry/resource review.
6. repositories.py/autofix_recovery.py/regression.py/intelligence/routes.py and RepositoryPanel/RecoveryPanel/RetestPanel: complete staging deployment identity, broader patch coverage, approved deployment-specific rollback and scan/AutoFix/retest browser journey. Do not merge/deploy automatically.
7. evidence_vault.py: retention/legal holds/broader records; crm.py: consent withdrawal/onboarding; reporting.py: missing report types; operations.py: controls/feature flags/sensitive-action MFA. Validate new UI.
8. Final integration, security review, documentation and cloud acceptance; then a completed release ZIP. Current handoff is not that release.

## Do not repeat immediately
Historical successful backend281/249, frontend69, Firebase/health browser, PostgreSQL/Redis/Mailpit and PHP contract checks need not repeat just for context. Rerun affected tests after changes: scope/worker -> scope/assessment/crawler/API/retest; schema -> migrations/PostgreSQL; mail -> consent/retry/Mailpit; GitHub/AutoFix -> repository/recovery; permissions -> tenant/agency; UI -> components/typecheck/browser. Full release integration remains necessary later.

## Preserved requirements
Payments/pricing/billing off, demo on, conversational assistant disabled pending strict evaluation. Scan/AutoFix separate; ownership, discovery, assessment and edits require their own scope. No unsolicited messages, paid-service activation or third-party assessments. Commit meaningful work and keep secret-free verified backups outside temporary storage.

## Latest runtime reproduction notes
WordPress runtime used WordPress7.1.3, official sqlite-database-integration3.1.1 and PHP8.5.12 with pdo_sqlite/sqlite3/mbstring extensions. Set AEGIS_WORDPRESS_ROOT to an isolated installation, install integrations/wordpress/aegis-verify/aegis-verify.php there, configure SQLite outside the webroot and block external HTTP/cron/email. Run php tests/wordpress_runtime.php. Runtime dependencies, database and wp-config secrets are intentionally excluded; recreate only this fixture, not the project. The test currently fails at bootstrap; inspect PHP error logging before asserting plugin outcomes.
On this Windows machine Vitest initially failed with EPERM cache rename; retry passed after TEMP and TMP were set to a new writable directory outside source, with --configLoader native --maxWorkers=2. Both logs retained. Notification crash/retry fixes and PostgreSQL014–016 validation remain NEXT WORK, not completed changes.

## Newest checkpoint overrides above email-next-work note
Current repository: aegis-latest, restored from supplied history tip 8a71b68. Notification final-claim crash recovery and broker batch continuation are implemented; 4 focused tests passed, Mailpit integration skipped. Do not repeat this unchanged set merely to resume. Next: validate PostgreSQL014–016 when isolated PostgreSQL is available; diagnose WordPress bootstrap with a PHP runtime; finish module/browser gaps listed above. Preserve SMTP at-least-once disclosure; stable Message-ID is not an exactly-once guarantee.
CRM consent withdrawal API/UI now implemented and focused-tested; do not rebuild it. Next code review: Launch Guard malformed-provider payload and role-downgrade handling, then final current-tree regression/build. PostgreSQL/PHP service prerequisites remain unavailable in this runtime.
Launch Guard malformed-provider/role-downgrade hardening is now focused-tested (23 passed). Full current build/regression results must be read from subsequent evidence, not assumed from this checkpoint. Next unfinished requirements remain PostgreSQL014–016, WordPress runtime, full browser journeys and the module matrix above.

Recovery packaging: after committing, `python scripts/export-recovery.py /absolute/output/directory` creates a ZIP, complete Git bundle and SHA256 sums. It refuses dirty worktrees and checks a fresh bundle clone and extracted source bytes. The bundle is also embedded in the ZIP. RECOVERY_VERIFICATION.json at ZIP root is authoritative for the new checkpoint; HANDOFF_METADATA.json and SOURCE-MANIFEST.json inside source describe the original incoming transfer, not the new export.
