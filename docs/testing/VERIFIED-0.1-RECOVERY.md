# Version 0.1 stabilization evidence — 2026-10-27

This report refers to the recovered and committed source tree, not the missing uncommitted additions from the interrupted workspace. It is not a production-release approval.

| Module | Implemented scope | Executed evidence | Result / remaining limits |
|---|---|---|---|
| Authentication | Native sessions, verification/reset, MFA; optional Firebase adapter | recovered-regression.log | Native/fixture tests passed; live Firebase not verified |
| Organizations | Memberships, roles, invitations, tenant controls | recovered-regression.log | Passed covered tests |
| Asset authorization | Exact-origin ownership proof, expiring consent, scope guards | recovered-regression.log; recovered-discovery.log | Passed controlled tests |
| Assessments | Worker jobs, cancellation, up to three approved paths, recurring scopes | recovered-core.log; recovered-native-runtime.log | Passed; PostgreSQL deployment unverified |
| Page discovery | One explicitly authorized bounded root read, at most 30 candidate paths | recovered-discovery.log; recovered-web-final.log | 33 backend/transport tests passed; no recursive crawler |
| Findings / intelligence | Stored observations, histories, approved knowledge, advisory synchronization | recovered-regression.log | Covered deterministic tests passed; no live-feed completeness claim |
| Reports / remediation | PDF snapshots, quotations without payment, tasks, full supported retests | recovered-regression.log | Passed covered tests |
| Administration | Existing operational views and pause controls | recovered-regression.log; recovered-web-final.log | Passed covered tests |
| UI | Component interactions, TypeScript and production build | recovered-web-final.log; recovered-build.log | 59 component tests passed; browser/visual acceptance not executed |
| Native runtime | Real Next/FastAPI proxy, Redis/Celery worker, SMTP, signup/login/company/logout | recovered-native-runtime.log | 3 tests passed with temporary SQLite; not PostgreSQL or browser acceptance |
| Whole backend | Current recovered modules | recovered-regression.log/.xml; recovered-coverage.json | 236 passed, 2 skipped; 91.95% measured statement coverage |

The two skipped tests are opt-in real Redis/native runtime tests. They were executed separately using the temporary Redis runner, which passed all three selected tests.

No payment processing was added or activated. No customer website was assessed or modified by these tests. GitHub live verification has been excluded from the current completion blockers at the user's direction; its existing source remains optional.

## Commands

From the source repository with the documented dependencies installed:

```bash
python -m pytest tests --cov=aegis --cov-fail-under=85
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
AEGIS_NATIVE_SMOKE=1 REDIS_SERVER_BINARY=/path/to/redis-server python scripts/test-with-redis.py
```

Use DEPLOY.md for native Linux backend and Vercel frontend deployment. Vercel still needs a real HTTPS API host. Firebase public browser configuration is retained, but it does not provision PostgreSQL, Redis, workers or server credentials.

## Outstanding before a production claim

Real PostgreSQL-integrated runtime and concurrency verification; authenticated Firebase live sign-in/server validation; browser acceptance; security review of the actual deployed environment. No observed tool exhaustion is claimed. The observed workspace recovery issue and PostgreSQL installation restriction are specific limitations, not evidence all remaining software work is complete.

## Scope for 0.2

Expanded provider-based SmartVerify, recursive crawling, agency delegation/branding, API-specific assessment profiles, full Launch Guard, continuous health monitoring, CRM, Recovery Guard and Safe Rollout remain unfinished. Earlier uncommitted health/Launch Guard additions were not recovered and are not represented as delivered here. The conversational AI assistant remains disabled pending quality evaluation.


## Authenticated Firebase verification completed
Firebase CLI authenticated successfully. Authenticated project listing returned aegis-d034c / AEGIS / ACTIVE. The live web-app SDK configuration was retrieved and compared with the supplied project/app configuration; see firebase-live-project-check.json for the exact comparison flags. No deployment or billing change occurred. This supersedes earlier statements that account/project access was unavailable. Application sign-in, backend Admin credential validation and end-to-end Firebase session creation remain unverified.

Additional actual HTTP discovery integration: recovered-real-discovery.log, 10 tests passed. The owned target received only its ownership challenge and one root discovery request; discovered links were not fetched.
