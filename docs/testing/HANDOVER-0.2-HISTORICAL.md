# AEGIS Security Cloud — 0.2 engineering handover

22 October 2026. **Local engineering checkpoint; not a completed production product or pilot-ready release.** Payments remain disabled in code. No public deployment or public-target assessment was performed. The full master specification and the new intelligence requirements are only partially fulfilled; the implemented/tested subsets and gaps are explicit below.

## Module evidence

| Module | Implemented | Tests run | Result | Remaining issues |
|---|---|---|---|---|
| Authentication | Yes, core | Foundation/API security tests | Pass tested subset | MFA, profile lifecycle, actual email/Redis integration |
| Organization Management | Yes, core | Membership, roles, tenant rejection | Pass tested subset | Invitation acceptance, management lifecycle, PostgreSQL concurrency |
| Domain Verification | Yes, DNS/file/meta | Scope/SSRF checks and real local HTTP ownership fixture | Pass tested subset | Live DNS, admin approval, arbitrary path scopes |
| Assessment Engine | Yes, bounded root profile | Worker lifecycle, failures, cancellation, local HTTP, in-memory Celery | Pass tested subset | Docker/Redis/PostgreSQL and full TLS matrix blocked |
| Findings Management | Yes, core | Dedup, histories, resolution, reopening, unsupported-check evidence | Pass tested subset | Full taxonomy, pagination/history UI, broader detectors |
| AI Reporting | Deterministic fallback and approved knowledge retrieval | Revision approval/invalidation, grounded patch guidance, unsupported claims | Pass fallback | External/local AI providers and provider injection/timeout matrix absent |
| PDF Reports | Yes, combined assessment and comparison | PDF route assertions and rendered three-page then corrected two-page retest review | Pass tested subset | Quote/progress/final summary formats, long-report stress |
| Remediation Management | Yes, core plus full-profile retest gates | Quote/acceptance, evidence, approval, six-check success, failed fix, new regression, unverified checks | Pass tested subset | No repository connection, patch generation, production deployment or bulk task workflow |
| Admin Panel | Yes, core | Roles, pause, source/revision/rule controls | Pass tested subset | Complete operational integrations/dashboard |
| UI/UX | Yes, core and intelligence section | 7 React interaction tests, TypeScript, Next build | Pass automated subset | Browser visual/mobile/accessibility gate blocked; no screenshots claimed |
| End-to-End Workflow | Partial API/worker integration | Controlled fixture and mocked-advisory workflows | Pass isolated subset / full stack blocked | Complete real-browser 25-step journey not executed |
| Intelligence synchronization | Four source adapters and persistent retries | Normalization, provenance checks, duplicate revisions, atomic failures, checkpoints | Pass deterministic subset | Live CISA retrieval blocked; no live source reliability claim |
| Inventory impact & notifications | Yes, supported metadata matching | Version boundaries, unknown semantics, manifest import, dedup, tenant isolation | Pass tested subset | No advisory-specific runtime vulnerability confirmation |
| Monitoring & retest comparison | Yes, recurring consent, scheduler, outbox and comparison | Expiry/revocation, proof recheck, duplicate suppression, dispatch retry and regression reports | Pass isolated subset | Real broker/beat restart, multi-process concurrency, custom calendar windows |

The source tree contains actual services, database migrations and API-connected UI. Test fixtures are explicitly isolated. No synthetic advisory is silently shown as a real feed result.

## Evidence and commands

Measured results: **74 backend tests passed**, zero failures/errors, 33.07 seconds; **88.81% statement coverage** (CLI excluded). **7 frontend tests passed**; TypeScript and Next production build passed. Build-reported first-load JavaScript is 107 kB landing / 120 kB console; no browser performance claim.

Current totals are in `docs/testing/STATUS.json`; raw results in `backend-full.txt`, `junit.xml`, `coverage.json`, `frontend-tests.txt`, `intelligence-typescript.txt`, `next-build.txt`, `ruff.txt` and `live-feed-check.txt`. The earlier checkpoint and its audits are retained in `docs/testing/HANDOVER-0.1.md`; its totals are historical, not current.

From the repository root, local startup:

```powershell
Copy-Item .env.example .env
# Edit .env and replace the local database password.
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api worker scheduler intelligence-worker migrate
```

Open http://localhost:3000, email inbox http://localhost:8025, API docs http://localhost:8000/docs. Stop with `docker compose down` (preserves volumes). Existing installations upgrade through the migration service to `002_intelligence`. Full Windows prerequisites, administrator promotion and ownership fixture procedure are in `README.md`.

Tests after installing `apps/api/requirements-dev.txt` and running `npm ci` under `apps/web`:

```text
python -m pytest --cov=aegis --cov-report=term --junitxml=docs/testing/junit.xml
python -m ruff check apps/api tests
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
```

## New lifecycle and limitations

Official-source retrieval → immutable revision → approved knowledge → local inventory matching → tenant notification → currently authorized assessment → engineer guidance → recorded approved staging change → complete applicable supported profile → resolved/unresolved/new/unverified comparison → continued opted-in monitoring.

“Complete profile” means all applicable supported root-response checks, not comprehensive penetration testing. Unsupported prior observations and advisory-specific runtime checks remain unverified. Missing Set-Cookie does not prove cookie flags fixed. A successful original retest cannot close a task while regressions, unresolved observations or verification gaps remain. No live website is modified by this software.

See `docs/architecture/INTELLIGENCE.md` for source coverage and boundaries. CISA catalog, incremental NVD/GitHub and known-GHSA OSV refresh are implemented; direct CVE.org/vendor/research/OWASP ingestion and comprehensive historical imports are deferred. Source authenticity is not independent proof of every claim. New detector activation requires reviewed shipped code, controlled fixture validation and admin approval. Knowledge updates do not retrain model weights.

## Release blockers and deferred scope

Docker, PostgreSQL, Redis and actual Celery beat/queue deployment could not run here. Browser observation was denied by environment policy; no bypass attempted. Live CISA transport did not pass the current environment's destination safeguards. These are blocked gates, not successful integrations.

All original gaps in the historical 0.1 handover remain except the new notification records/UI, recurring consent, full retest evidence/comparison, and outbox for scheduled/retest jobs. Original on-demand submission still needs outbox migration. Scanner process/credentials separation, production ingress, actual egress validation, dependency audit refresh before release, backup restoration, file storage/uploads, identity lifecycle, complete reporting types, custom scope/window support, production monitoring, large-catalog performance and independent security review remain required. New knowledge retrieval scans current approved records and is not yet optimized for a large catalog.

There is no active LLM, no repository/patch integration, no automatic deployment, and no payment provider. Accepting a quotation never represents collected money. Current status: **ready to inspect and run isolated local engineering tests; full Compose startup remains unverified, external pilot and production approval blocked.**
