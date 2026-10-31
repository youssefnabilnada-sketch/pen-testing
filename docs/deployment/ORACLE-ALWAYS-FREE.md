# OCI Always Free deployment preparation — review, not production approval

Status: Only GitHub code preparation. No Oracle account, VM, DNS, database, service or public deployment was created. Preserve the existing Vercel project and the fail-closed HTTPS API requirement.

## Resource and eligibility guardrails
Use only assets explicitly marked **Always Free Eligible** in the OCI account's **home region**. Oracle's published Always Free tenancy limits (as of October 2026): an A1 Flex VM allowance equivalent to **2 OCPUs / 12 GiB RAM** (1,500 OCPU-hours / 9,000 GB-hours monthly), plus 200 GB total eligible block-volume storage inclusive of boot volumes. Limits/availability can change. A1 allocation may fail with "out of host capacity" and idle VMs can be reclaimed. No PAYG upgrade, marketplace images, paid networking or add-ons are authorized by this guide. Do not circumvent account age, identity, address, credit-card or eligibility checks.

Official source: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

## Intended architecture
- Existing Vercel **pen-testing** project: Next.js in `apps/web`, Node 22, `npm ci`, `npm run build`; no separate Next service on the VM.
- OCI Always Free A1 Linux VM: FastAPI behind HTTPS Caddy, dedicated low-concurrency Celery scanner, intelligence, notifier, scheduler; local PostgreSQL and Redis restricted to loopback.
- Public access through **only** 443 (and 80 solely for TLS validation/redirect) with a DNS hostname `api.<owned-domain>`. Tighten inbound SSH to operator-controlled source addresses. Do not expose 8000/5432/6379.
- Firewall and outbound egress filters must enforce authorized-scope scanning and keep metadata/private addresses inaccessible; application code alone is insufficient.
- Preserve durable storage and backups; a 50 GiB boot volume counts toward the 200 GB allocation.
- `WEB_ORIGIN` equals the eventual Vercel production HTTPS origin. On Vercel set **server-side** `API_INTERNAL_URL` to the live API HTTPS **origin**; never public-prefix it. Keep the frontend build guard in `apps/web/lib/deployment.ts`.
- Never publish a public assessment service until scoped-asset verification, tenant separation, Firebase session flow, workers, migrations, email provider and recovery tests pass.

## Operator steps — only after an eligible account/VM exists
1. Using an authorized account owner, provision **one** Always Free Eligible Ubuntu ARM64 image, A1 Flex shape at **2 OCPU, 12 GB** maximum (or less as available), in the home region. Check the displayed cost is $0 and stop if not. Configure SSH key access with no password login; don't paste private keys into chat or GitHub.
2. Install Python **3.12**, PostgreSQL, Redis and Caddy via supported OS packages or trusted sources; use Ubuntu apt where appropriate. Check `python3.12 --version` and `uname -m` is `aarch64`.
3. Obtain repository source from the user's GitHub with a least-privileged read connection. Run `bash scripts/build-oci-backend.sh` as an **unprivileged** user; this only creates `.venv` and checks imports. Do **not** run `scripts/build-server.sh`: it needlessly builds Next.js.
4. Configure OS hardening and least-privileged service accounts using existing `infrastructure/deployment/aegis@.service`, `aegis-migrate.service` and `Caddyfile.api`. The 768 MB per-service MemoryMax setting may need performance validation on an A1 VM. Review SSRF defenses and block VM metadata/private-network access.
5. Create local PostgreSQL role/database and secure Redis on localhost only. Store secrets solely in root-controlled `/etc/aegis/*.env` with correct owner/group permissions. Set `AEGIS_ENV=production`, valid Postgres `DATABASE_URL`, `REDIS_URL`, `COOKIE_SECURE=true`, `LOCAL_FIXTURE_MODE=false`, `WEB_ORIGIN=https://...`, and payment/AI feature flags **disabled**. Provide a Firebase credential via managed secret-file mechanism; configure SMTP and independent MFA encryption secret. Never upload these to source, chat, or web browser.
6. Set `AEGIS_API_DOMAIN` to a DNS-resolving owned HTTPS hostname and validate the Caddy config before starting. If no hostname is available, do not spoof one or disable TLS.
7. Back up database, then start a **single** migration service `aegis-migrate` and only proceed if successful. Start API, scanner, intelligence, notifier and **one** scheduler; inspect logs. Verify `/ready`, real Firebase login, email, tenant isolation and an explicitly authorized staging target. Validate backup restore to an isolated database.
8. After API readiness, configure Vercel's `API_INTERNAL_URL` and redeploy the existing project. Keep it protected/private during acceptance; avoid opening customer access until acceptance checklist has been signed off.

## Unresolved blockers
Oracle account/eligible VM and public hostname are **not connected** to ChatGPT; no OCI management integration is available in this chat. The account owner must complete the provider's own legitimate signup and VM provisioning, complying with provider terms. Host/instance identity, DNS, Firebase Auth deployment setup, SMTP, secret management, reverse proxy, verified backups, full PostgreSQL/browser and independent security acceptance are unverified. No production deployment should be claimed.

Relevant internal docs: `DEPLOYMENT_HANDOFF.md`, `DEPLOYMENT_GUIDE.md`, `docs/deployment/PRODUCTION-CHECKLIST.md`.
