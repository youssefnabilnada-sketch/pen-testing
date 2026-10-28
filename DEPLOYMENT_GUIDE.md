# GitHub and Vercel deployment

This repository continues the supplied AEGIS application. Upload the source directory contents to a private GitHub repository; do not upload local secrets or generated dependencies. Vercel runs `apps/web`. The API and background services require a separate host. This guide is configuration, not evidence of a completed production deployment.

## Frontend
1. Import your GitHub repository into Vercel.
2. Choose **Next.js** and set **Root Directory** to `apps/web`.
3. Use `npm ci` for installation and `npm run build` for the build. Keep the supplied `package-lock.json`.
4. Set server-side `API_INTERNAL_URL` to your actual backend HTTPS origin, for example `https://api.your-domain.example`, without a path or credentials. Do not prefix it with `NEXT_PUBLIC_`.
5. Deploy after the backend is healthy. The build intentionally refuses a Vercel deployment without an HTTPS API origin. This prevents publishing an apparently working console connected to localhost.
6. Set backend `WEB_ORIGIN` to the exact final Vercel/custom origin. Frontend calls use the same-origin `/api` proxy, including HTTP-only session cookies.

## Backend without Docker
The existing `DEPLOY.md`, `scripts/build-server.sh`, systemd units and Caddy configuration describe a native Linux deployment. One operator-managed Linux server can host FastAPI, PostgreSQL, Redis, scanner, intelligence worker and scheduler. Protect the database/queue on private interfaces; only Caddy's HTTPS listener should be public. Take and restore-test database backups before admitting customer data.

For a managed host, configure these processes from the repository root:

| Process | Command |
|---|---|
| Install | `pip install -r apps/api/requirements.txt -r apps/api/requirements-firebase.txt` |
| Migrate once before release | `alembic -c apps/api/alembic.ini upgrade head` |
| API | `uvicorn aegis.main:app --host 0.0.0.0 --port $PORT` |
| Scanner | `celery -A aegis.worker.celery worker --loglevel=INFO --concurrency=1 --hostname=scanner@%h` |
| Intelligence | `celery -A aegis.worker.celery worker -Q intelligence --loglevel=INFO --concurrency=1 --hostname=intelligence@%h` |
| Scheduler (one instance) | `celery -A aegis.worker.celery beat --loglevel=INFO --schedule=/tmp/aegis-beat` |

Set `PYTHONPATH=apps/api` for all backend commands. Use PostgreSQL and Redis services with persistent storage, restart policies, private networking and backups. Health checks: `/health` for API process liveness and `/ready` for database schema plus Redis readiness. Test worker availability separately through administrator diagnostics.

Required production settings are in `infrastructure/deployment/production.env.example` and `worker.env.example`. Keep `AEGIS_ENV=production`, `COOKIE_SECURE=true`, `LOCAL_FIXTURE_MODE=false`, `PAYMENTS_ENABLED=false`, `BILLING_MODE=disabled`, and `AI_ASSISTANT_ENABLED=false`. Never set `TESTING=1` or Firebase emulator settings in production.

## Firebase
Existing public web settings are in `packages/configuration/firebase.public.json` for project `aegis-d034c`. They are not administrative credentials. Enable your intended Auth providers and add the exact frontend hostname in Firebase authorized domains.

Provide backend credentials using the hosting platform's secret-file interface or workload identity. `GOOGLE_APPLICATION_CREDENTIALS` must point to a file outside the repository. Grant only the required Firebase Auth access. Never paste the private key into chat, browser variables, Git or archives. Application sign-in and revocation require live validation after deployment.

For isolated local identity development, use `infrastructure/firebase-emulator/firebase.json` and `local.env.example` with the synthetic `demo-aegis` project. Start `firebase emulators:start --only auth --project demo-aegis --config infrastructure/firebase-emulator/firebase.json`. This does not create or replace the live Firebase project. The adapter accepts emulator mode only with explicit local development settings; public deployments fail closed. Emulator mail actions are viewed through emulator tooling, not a real inbox. See [Firebase emulator guidance](https://firebase.google.com/docs/emulator-suite/connect_auth).

## Email
Use existing Mailpit configuration for local mail, or the existing loopback SMTP tests. For production set SMTP host, port, sender and credentials securely, with `SMTP_TLS=starttls` or `implicit`. Verify the sender domain with your chosen provider. Provider acceptance is not confirmed inbox delivery. No sender/provider has been provisioned.

## Hosting selection
The supplied native Linux path can consolidate services on one server. A managed alternative is Render's separate web, worker, PostgreSQL and Key Value services; assess the full service cost before creation. Its documented worker plans are paid, so no free always-on full-stack promise is made. No resources were activated. See [Render service configuration](https://render.com/docs/blueprint-spec).

## Acceptance before publication
Run the included backend/frontend tests and PostgreSQL/Redis CI jobs; then verify real Firebase registration/login/recovery, transactional mail, owned-target authorization, worker execution, stored reports, cancellation and cross-tenant isolation on the deployed environment. Browser smoke tests alone are not whole-product acceptance. Review PROJECT_STATUS.md for current gaps before admitting customers.
