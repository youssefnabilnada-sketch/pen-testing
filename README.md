# AEGIS Security Cloud — development source

**An integrated local-development implementation, not the complete production product.** See `docs/testing/VERIFIED-0.1-RECOVERY.md` and `RECOVERY-CHECKPOINT.md` for the current recovered source and executed verification. `HANDOVER.md` records earlier checkpoints. No public deployment has been performed. Payments are disabled in code, not merely hidden in the interface.

## Upload / online deployment

Use [DEPLOY.md](DEPLOY.md) for Vercel frontend + Firebase identity + native Linux backend, or a single Linux HTTPS host. Docker is not required for this deployment path. Actual backend hosting and server-side credentials must be provisioned; none has been connected or billed by this source archive.

## What is connected

Next.js/React/TypeScript customer console and landing page → FastAPI → SQLAlchemy → PostgreSQL (Compose), Redis → Celery assessment worker. Local email: Mailpit. Reports: immutable database snapshots rendered to PDF. Development tests use SQLite, controlled fixtures and a real in-memory Celery worker; that does not validate PostgreSQL or Redis behavior.

The operational core includes account registration/verification/login/reset, organization membership, exact-origin ownership challenges, authorization records, bounded root-response checks, job tracking/cancellation, findings/history/retests, PDF reports, deterministic explanations, remediation requests, administrator quotations, customer acceptance, task transitions, conversations, audit events and administrative pause.

### Supported assessment scope

One GET per explicitly authorized path, up to three simple paths on the exact origin. Optional separately authorized discovery reads at most 64 KiB of root HTML and lists up to 30 same-origin candidate paths without fetching them. Candidate paths require separate assessment approval. No redirect following, recursive crawling, authenticated application assessment or implicit subdomains. TLS certificate trust/hostname verification uses Python's default trust store. A certificate validation failure fails the assessment; it is not yet normalized into a certificate finding. Expiring valid certificates can produce observations. No CVSS scores or exploitability claims are generated.

## Legacy local test setup (not online deployment)

Prerequisites: Docker Desktop running Linux containers (with WSL2 as appropriate), a terminal, approximately 4 GB free RAM for containers, and internet access to download packages/images. No hosting, AI subscription or payment credentials required. Installation downloads are required; this archive does not bundle Docker or dependencies.

In PowerShell, from the extracted repository:

```powershell
Copy-Item .env.example .env
notepad .env
# Replace POSTGRES_PASSWORD with a long random LOCAL development password.
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api worker migrate scheduler intelligence-worker
```

Migration runs automatically in the one-shot `migrate` container. Open:

- Application: http://localhost:3000
- Local email inbox: http://localhost:8025
- API documentation: http://localhost:8000/docs

Register an account and open the verification link in your email; the token is prefilled and you confirm the form. For legacy local tests the message is in Mailpit; copying the one-time token into **Verify email** remains supported. Then sign in and create a company.

Create a separate administrator account through the same registration/verification flow. Promote that verified local account explicitly:

```powershell
docker compose exec api python -m aegis.cli promote-admin admin@example.test
```

No default administrator or password is supplied. Sign out and sign back in after promotion.

### First authorized test

1. In Assets, register `http://fixture`. It is reachable only inside the isolated Compose target network.
2. Choose **HTML verification file** and create a challenge.
3. Copy only the token from the instruction into `infrastructure/fixture/config.json`, preserving JSON formatting:

```json
{"verification_token":"PASTE_THE_ACTUAL_CHALLENGE_TOKEN_HERE","hardened":false}
```

4. Click **Check ownership**. The fixture serves that exact token; no ownership bypass is used.
5. Read the exact scope and check the authorization box, then launch.
6. Follow the real assessment status, review findings and download its PDF.
7. Request remediation from a finding such as missing CSP.
8. As the platform administrator, issue a formal quotation in Administration.
9. As the customer, accept the scope. No payment is collected.
10. Assign the task, begin work, then change the local fixture's `hardened` value to `true`. This is an approved change to an isolated test target, not a production website.
11. Open Applied-change evidence & full security retest. Record the authorized fixture change, rollback plan and staging evidence.
12. As the customer Owner/Admin, approve the pending retest and full scope after the 60-second cooldown. Inspect Threat Intelligence → Retest history and download the comparison report. The HTTP observation remains unresolved on this HTTP fixture, so full task closure remains blocked. The automated HTTPS-response fixture separately tests successful closure.

The fixture exception is **exactly** `http://fixture` resolving only to `172.29.0.10`, with `LOCAL_FIXTURE_MODE=true`. It does not permit arbitrary localhost/private scans. Scanner/target networks are internal and published ports bind only to 127.0.0.1. Only the separate intelligence worker has outbound advisory-source access. Public-site assessments cannot run in this isolated Compose profile. Do not remove isolation to make an unreviewed public service available.

### Operations

```powershell
# Apply migrations explicitly if needed
docker compose run --rm migrate
# Inspect scanner failures
docker compose logs --tail=200 worker
# Stop services, retaining data
docker compose down
# Restart retained data
docker compose up -d
```

Do not use `docker compose down -v` unless intentionally deleting your local database and queue volumes.

## Tests without Docker

Python 3.12 and Node 22+ are required. PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r apps/api/requirements-dev.txt
python -m pytest --cov=aegis --cov-report=term-missing --junitxml=docs/testing/backend-junit.xml
python -m ruff check apps/api tests
Set-Location apps/web
npm ci
npm test
npm run typecheck
npm run build
Set-Location ../..
```

If PowerShell activation is restricted, invoke `.venv\Scripts\python.exe` directly. Unix equivalents use `python3 -m venv .venv` and `.venv/bin/python`.

Browser smoke tests against a running Compose application:

```powershell
Set-Location apps/web
npx playwright install chromium
npm run e2e
```

These smoke tests cover navigation, account form, narrow viewport overflow and reduced motion. They are **not** the complete 25-step acceptance scenario. That full scenario remains a release gate; see `docs/testing/COMPOSE-ACCEPTANCE.md`.

## Troubleshooting

- Docker command unavailable: install/start Docker Desktop and confirm Linux containers; Docker was unavailable in the build environment, so this Compose setup still requires execution on a Docker host.
- Email unavailable: inspect `mailpit` and `api` logs; registration fails closed on delivery error.
- 503 on login: check Redis health; authentication throttling intentionally fails closed when Redis is unavailable.
- No assessment running: check worker logs, the admin pause flag and queue health. Jobs left active after a worker crash can be marked failed with **Recover stale jobs** after five minutes. They are not silently retried against a target.
- Fixture verification fails: verify the exact token and subnet, challenge expiry, file mount and `LOCAL_FIXTURE_MODE`. No global private-address bypass should be added.
- Redirect rejected: add and verify the final origin separately. Redirect following is outside this build's scope.
- Port/subnet conflict: choose another host port and adjust WEB_ORIGIN. Changing the fixture subnet also requires reviewed changes to its exact IP guard and tests.
- No findings: distinguish pending/failed/cancelled jobs from completed assessments. No supported findings does not certify security.

## Repository

Backend modules live together in `apps/api/aegis` to avoid unnecessary microservices. API and worker use separate processes from the same image. `models.py` and Alembic contain the relational schema; `safety.py` owns the only assessment HTTP transport; `checks.py` owns deterministic detectors; `analyst.py` owns the explanation boundary; `reporting.py` renders immutable snapshots. `billing.py` has future interfaces and a provider that always rejects checkout creation.

The worker and scanner are a single service in this checkpoint. Stronger process/network/DB credential separation is required before pilot use. See the threat model and deployment checklist.

## Continuous intelligence and monitoring

Compose starts `scheduler` (Celery beat) and `intelligence-worker` (dedicated queue). Apply migration `002_intelligence` with the normal migrate command. Open **Threat Intelligence** for global advisories, source health, declared inventory, approved knowledge, schedules, notifications and retest history. A platform administrator reviews knowledge revisions and validates/approves code-owned detection candidates. No seed advisories are shown as real customer results.

Default source synchronization is every 6 hours; administrators can configure 6–12 hours. Public feed availability and running services are required. Manual **Sync now** records success only after execution. Monitoring requires explicit recurring consent; existing ownership proof must remain published for re-verification. See `docs/architecture/INTELLIGENCE.md` for source coverage and unsupported version semantics.

Focused extension tests: `python -m pytest tests/test_intelligence.py tests/test_monitoring_regression.py`. Full backend: `python -m pytest --cov=aegis --cov-report=term`. Frontend: `npm --prefix apps/web test`.

## 0.3 incremental update
See [UPGRADE-0.3.md](UPGRADE-0.3.md) for new ownership assistance, one-click engineer
review, optional Firebase identity boundaries, upgrade instructions and limitations.
This is a development checkpoint; cloud hosting and automatic fixes are not complete.

## 0.4 Firebase identity UI
See [UPGRADE-0.4.md](UPGRADE-0.4.md). Google/email controls, explicit registration and
account linking are now implemented with deterministic tests. Live cloud integration,
visual acceptance and the rest of the full SaaS scope remain incomplete. Payments disabled.

## Current release status
[CURRENT-STATUS.md](CURRENT-STATUS.md) is the authoritative current status, including
unfinished requirements and blocked acceptance. Historical checkpoint documents are
not claims that the complete product is ready.

Account lifecycle, bounded evidence attachments, personal alerts and permitted monitoring windows: see `docs/api/ACCOUNT-EVIDENCE-WINDOWS.md`. Current implementation status is in `CURRENT-STATUS.md`; source availability is not a production-readiness certification.
