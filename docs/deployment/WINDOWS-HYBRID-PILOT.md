# AEGIS — isolated Windows pilot while Oracle provisioning is pending

This is a **local engineering pilot**, not a public or production deployment.
The current public-facing Vercel preview stays unchanged. No cloud credentials,
DNS records, home-router port forwarding, production database, or real customer
information is used or changed by these scripts.

## Requirements

- Windows 11 (or supported Windows 10 configuration) with WSL 2 and **Docker Desktop** running in Linux-container mode.
- Git for Windows; at least 15–25 GB free disk, and sufficient unused system RAM.
- Verify Docker Desktop is working using `docker info` and `docker compose version`.
- Review the script before running it. The scripts do not install Docker or Git.

## Keep your current working copy safe

Use a **separate directory** so any previous AEGIS files, .env, databases,
containers or in-progress changes are not overwritten:

```powershell
git clone --single-branch --branch deploy/windows-hybrid-pilot-20261029 https://github.com/youssefnabilnada-sketch/pen-testing.git AEGIS-Pilot
cd AEGIS-Pilot
powershell -NoProfile -File .\scripts\windows\Start-AegisPilot.ps1
```

The script:
1. Checks that Docker and Docker Compose are available.
2. Creates an ignored local `.env` **only if none exists**; uses a cryptographically random DB password and safe local testing switches.
3. Starts Postgres, Redis, local fake SMTP (Mailpit) and an isolated owned fixture using the dedicated Compose project name `aegis-pilot`.
4. Applies Alembic migrations for **only** this pilot database.
5. Starts the local API, Next.js web, scanner worker, intelligence worker and scheduler.
6. Checks `http://127.0.0.1:8000/health` and reports Compose container state. A healthy API alone does **not** verify every workflow.

Open (only on this PC):
- Web UI: http://localhost:3000
- API health: http://127.0.0.1:8000/health
- Local test email inbox: http://localhost:8025

**Never forward router ports 3000, 8000, 8025, 5432 or 6379 to the Internet.**
The repository binds HTTP only to loopback; PostgreSQL and Redis have no host
ports. Cloudflare Tunnel/Tailscale/public access are deliberately *not* enabled
by these scripts.

## Useful commands

Status (read-only):
```powershell
powershell -NoProfile -File .\scripts\windows\Start-AegisPilot.ps1 -StatusOnly
```

Logs (inspect locally and redact private data before sharing):
```powershell
docker compose --project-name aegis-pilot -f docker-compose.yml -f docker-compose.local-access.yml logs --tail=80 api worker intelligence-worker scheduler
```

Stop the pilot safely (preserves volumes):
```powershell
powershell -NoProfile -File .\scripts\windows\Stop-AegisPilot.ps1
```

**Never run** `docker compose down -v` for this project; that deletes persistent
database volumes. A new deployment must include encrypted backups and restore tests.

## Hybrid cloud migration — next phase, not yet executed

After Oracle account access and secure server provisioning:

1. Deploy **production-only** FastAPI, PostgreSQL, Redis, notifier and scheduler to Oracle, with proper credentials, certificate, backup/restore tests and approved migration. Keep the pilot data isolated; don't promote test data to production.
2. Enable Firebase Authentication, HTTPS cookies, actual transactional SMTP, MFA encryption, worker service accounts, auditing and production runtime validation; never send secrets through chat or commit them.
3. Use a mutually authenticated/private encrypted network between the server and a **dedicated** PC worker (for example a carefully configured Tailscale network). Do not expose Redis or PostgreSQL to the public Internet.
4. Give Windows worker an isolated non-admin runtime without full access to the owner's desktop/files. Design dedicated job queues and minimum database privileges. The current worker uses DB and Redis and is not yet safe to attach remotely without code and firewall changes.
5. Add heartbeats, timeouts, retries, outage behavior and graceful shutdown. Re-test authorized assessment scope, SSRF controls, task idempotency, isolation and FastFix approval gates.
6. Set Vercel server-only `API_INTERNAL_URL` to the *real, tested* HTTPS backend hostname, redeploy and validate browser auth/report/downloads. Backend `WEB_ORIGIN` must equal the final frontend origin. Avoid deploying with `localhost` or with test-mode flags.
7. Conduct independent security review and end-to-end checks **before** opening registration or allowing real customer security assessments. Existing `CURRENT-STATUS.md` documents incomplete features.

The existing GitHub project contains code and unit/regression test evidence, but not a verified public backend. A Windows PC cannot be controlled or configured by simply deploying GitHub files; the operator must run the local script. Oracle and Windows can later share work, but connecting public web traffic directly to a development stack would bypass its production security gate and is prohibited in this plan.

## Operational limitations

- Local fixture mode remains ON and Firebase production login remains OFF. Payments and AI integrations remain disabled. This is intentional for secure testing.
- Docker Desktop itself can consume several GB of RAM and disk.
- No guarantee of uninterrupted service or zero vulnerability is possible.
- The temporary Vercel URL is **not** wired to this local pilot.
