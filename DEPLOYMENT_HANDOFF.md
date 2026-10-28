# Deployment handoff — not a deployed or release-approved system

Intended architecture: Vercel frontend; cloud FastAPI, default-queue worker, intelligence worker and ONE scheduler; managed PostgreSQL and Redis; Firebase Auth; transactional SMTP. It must not depend on a personal computer. No production hosting was configured or verified.

## Local setup
Install Python3.12 and Node22+. Install backend requirements-dev.txt plus requirements-firebase.txt; npm ci in apps/web. Copy .env.example to a private .env and load its values into EACH service process; the commands below do not implicitly load every .env. Never commit secrets.
Docker option: `docker compose -f docker-compose.yml up --build` with supplied optional local-access/Firebase overlays as documented. Docker was unavailable in this session; native services were tested instead. No successful Compose run is claimed.
Native services: PostgreSQL17, Redis, Mailpit. Configure DATABASE_URL, REDIS_URL, PYTHONPATH=apps/api, WEB_ORIGIN=http://localhost:3000, COOKIE_SECURE=false, SMTP_HOST=127.0.0.1, SMTP_PORT=1025, SMTP_TLS=none. LOCAL_FIXTURE_MODE only allows the supplied isolated fixture, not arbitrary local targets. Keep test data separate.

From repository root, separate terminals:
```
python -m alembic -c apps/api/alembic.ini upgrade head
python -m uvicorn aegis.main:app --host 127.0.0.1 --port 8000
python -m celery -A aegis.worker.celery worker --pool=solo --concurrency=1 --loglevel=INFO
python -m celery -A aegis.worker.celery worker -Q intelligence --pool=solo --concurrency=1 --loglevel=INFO
python -m celery -A aegis.worker.celery beat --loglevel=INFO --schedule=./work/aegis-beat
```
Create work/ first. Solo pool is the Windows test choice; Linux uses supplied deployment configuration. Run one beat only. Default queue handles assessment/health/email; intelligence queue handles feeds. In apps/web set API_INTERNAL_URL=http://127.0.0.1:8000 and run npm run dev. For production builds use the supplied Next standalone build/server scripts; do not assume next start is the final standalone packaging method.

## Firebase
Project aegis-d034c and non-secret metadata remain in packages/configuration/firebase.public.json. The public API key was removed from this handoff at user request. Obtain authorized web configuration and supply FIREBASE_WEB_API_KEY/FIREBASE_WEB_APP_ID. Enable FIREBASE_AUTH_ENABLED only when configured. Backend credentials use workload identity or GOOGLE_APPLICATION_CREDENTIALS pointing to a secret file outside Git. Confirm providers, authorized domains and Auth permissions. Never put a service-account key in browser variables/chat/source.
Local: firebase emulators:start --only auth --project demo-aegis --config infrastructure/firebase-emulator/firebase.json, using local.env.example. Production rejects emulator settings. Live Firebase remains unverified.

## Email and GitHub
Mailpit SMTP1025/UI8025 is local only. Production: SMTP_HOST/PORT, SMTP_TLS=starttls or implicit, SMTP_USERNAME/PASSWORD, approved MAIL_FROM/domain; host secrets. Alerts default off; email tasks retry and report smtp_accepted, not inbox-confirmed.
GitHub requires an authorized App installed only on selected repos: GITHUB_ENABLED, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI and TOKEN_KEY (all prefixed GITHUB_). Existing patch flow needs contents/PR write and checks read; Launch Guard also reads commit statuses. User OAuth consent and MFA write approval remain separate. No live App/repository acceptance occurred. MFA_ENCRYPTION_KEY and GITHUB_TOKEN_KEY must be generated separately, securely stored and backed up with database recovery material.

## Vercel/cloud
Upload restored source to the user's GitHub. Vercel: Next.js, Root Directory apps/web, npm ci, npm run build. Set server-only API_INTERNAL_URL to actual backend HTTPS origin without path/credentials or NEXT_PUBLIC prefix. Build guard rejects missing/local/non-HTTPS Vercel backend. Backend WEB_ORIGIN must match exact final frontend origin.
Host API and workers separately; Vercel frontend alone cannot run this backend platform. Provision managed PostgreSQL/Redis with private networking/TLS and persistence. Configure AEGIS_ENV=production, PYTHONPATH=apps/api, DATABASE_URL (or DATABASE_* components), REDIS_URL, COOKIE_SECURE=true, LOCAL_FIXTURE_MODE=false. Unset TESTING and emulator variables. Preserve PAYMENTS_ENABLED=false, PRICING_ENABLED=false, BILLING_MODE=disabled, DEMO_ACCESS_ENABLED=true, AI_ASSISTANT_ENABLED=false and AI_PROVIDER_ENABLED=false. Examples: infrastructure/deployment/production.env.example, worker.env.example. Public Firebase key must be reconfigured.
Run Alembic once per release. API command: uvicorn aegis.main:app --host 0.0.0.0 --port <host-provided-port>. Production worker and scheduler commands are in DEPLOYMENT_GUIDE.md and scripts/server-process.py; systemd/Caddy examples are under infrastructure/deployment. Configure logs, dependency readiness, persistent scheduler state and secure backup/restore. Never expose DB/Redis publicly.

## Required before public use
Hosting accounts/budget approval, domains/TLS, Firebase settings/credentials, SMTP sender/provider, GitHub App setup, encryption/MFA secrets, database/key recovery validation, remaining feature/security/browser acceptance and owned-target production checks. No paid resources may be activated without approval. Provider settings should be checked against current official docs when deploying; no web re-research was needed for this export.

## Latest transfer
Use AEGIS_SECURITY_CLOUD_LATEST_TRANSFER.zip and AEGIS_SECURITY_CLOUD_TRANSFER_HISTORY.bundle. Restore the bundle to recover history; ZIP includes the same current source plus manifest/metadata. Runtime credentials/databases/dependencies are excluded. Transfer these files to the other account manually; persistence on this PC does not automatically grant another account access. Unfinished development; no production deployment validation. See current status and continuation documents.
