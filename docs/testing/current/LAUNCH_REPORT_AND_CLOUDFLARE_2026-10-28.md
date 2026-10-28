# AEGIS: Launch Guard PDF and Cloudflare response safety checkpoint

**Engineering evidence only — NOT a production release, penetration test, or public launch approval.** Based on previous Git checkpoint `2a9875b` with all source and history preserved.

## Implemented here

1. Cloudflare DNS TXT-only proof publisher: bounded streamed replies (4 KiB chunks, 64 KiB response cap), declared-size precheck, fixed external API, no redirects or environment proxies, IDNA canonicalization, strict record and pagination shape checks, safe failure on malformed data, revocation recheck even when proof already exists. Never grants scanning permission and never edits existing DNS records.
2. Launch Guard: new organization-scoped, authenticated `GET /launch-reviews/{review_id}/report.pdf`; reads a persisted exact-commit review, calls tenant membership authorization before rendering, outputs PDF with no-store/nosniff/attachment headers and explicit advisory limitations. No GitHub network call or deployment performed during export.
3. Customer console Launch Guard: download link to the PDF for each saved review, alongside retained on-screen evidence.
4. Standalone PDF tests cover successful bytes/text, HTML-like untrusted labels safely escaped, optional missing review fields, wrong-tenant rejection before rendering, and private download headers.

## Commands and exact verification

- `PYTHONPATH=apps/api python -m unittest discover -s tests -p 'test_*unit.py' -q` — **40 passed**.
- `PYTHONPATH=apps/api python -m unittest discover -s tests -p 'test_discovery_deadline.py' -q` — **4 passed**.
- `... -p 'test_crawler_html_resilience.py' -q` — **4 passed**.
- `... -p 'test_discovery_grants.py' -q` — **3 passed**.
- **51 distinct isolated Python tests passed**. These are NOT integrated FastAPI or full backend regression results.
- `php -l integrations/wordpress/aegis-verify/aegis-verify.php` and `php tests/wordpress_contract.php` — **passed** (isolated contract; no real WordPress bootstrap).
- `python -m compileall -q apps/api/aegis tests` — **passed**.
- Standalone global TypeScript `transpileModule` of `apps/web/app/console/LaunchPanel.tsx` — **passed** (only syntax; no Next/Vitest typecheck/build).
- Isolated SQLite Alembic `upgrade head`, `check`, `downgrade 013_agency`, `upgrade head`, `current` — **passed**, final revision `017_evidence_legal_holds` (NOT PostgreSQL proof).
- `git diff --check` — **passed**.

## Known external and engineering release blockers

- Full backend `pytest` collection fails on absent Celery in this execution container. An attempted dependency lookup supplied no Celery package. The last historical full backend run on a different tree had a failure related to changing Firebase test configuration; it was not rerun on a frozen current tree.
- `apps/web/node_modules` is unavailable; full TypeScript, Vitest, production Next.js build, Playwright and real browser review have not been run for the current tree.
- PostgreSQL 014–017 schema round-trip **on PostgreSQL**, operational backup restoration, Redis/Celery beat/worker integration, actual WordPress fixture, live scoped Cloudflare test zone, Firebase real login, email sender and live cloud integration remain unverified.
- SmartVerify provider choices beyond Cloudflare, end-to-end AutoFix staging identity/rollback, full Launch Guard/API/Agency/CRM/Vault/Admin/report acceptance, security review, accessibility, quota/rate limiting, monitoring and documented incident/privacy operations remain incomplete or not accepted.
- Actual public deployment requires a user-owned GitHub repo, hosting projects and safe credential configuration. Do not enable payments/pricing/chat assistant or scan any third-party site without separate explicit authorization.

## Next production acceptance sequence

1. Publish the exact archive to a user-owned **private** GitHub repository; run all supplied CI workflows, fix any failures, and preserve logs and commit hashes. Do not confuse passing unit tests with deployment acceptance.
2. Test isolated PostgreSQL/Redis/worker/beat, WordPress and a dedicated owner-controlled Cloudflare zone. Complete missing provider options or adjust beta scope transparently.
3. Execute complete Scan → owner permission → report → explicit AutoFix proposal → approved staging → full authorized retest → user-approved deployment/rollback and desktop/mobile browser journeys.
4. Run independent security/privacy review, backup restore, monitoring/alert tests, TLS/DNS/MFA provider validation and tenant isolation under deployed conditions.
5. Only when these gates pass, tag a release candidate for optional public pilot; release must not be described as ready before then.
