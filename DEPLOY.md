# Online deployment — native Linux, no Docker required

This is the primary deployment track. The Docker files are retained solely for older
installations and test compatibility; they are not the requested online deployment.
Source is ready to push to a private GitHub repository. The full product is not yet
release-approved: missing scope and evidence remain in CURRENT-STATUS.md.

## Services

One HTTPS domain -> Caddy -> Next.js UI and FastAPI `/api`. Durable PostgreSQL holds
organizations, verified assets, sessions, findings, intelligence, quotes and reports.
Redis coordinates Celery. Dedicated scanner, intelligence and scheduler processes run
as separate OS users. Firebase Auth supplies Google/email identity. Firebase Hosting
alone cannot run this Python/Celery architecture; uploading a repository is not a
deployment or a database connection. No Firestore migration has been performed.

## Server prerequisites and build

### Existing Vercel + Firebase accounts

Import the GitHub repository into Vercel with root directory `apps/web`.
Set `API_INTERNAL_URL=https://YOUR-ACTUAL-API-HOST` before building. Missing/local
API configuration intentionally fails a Vercel build; no disconnected localhost UI
should be published. There is no working API hostname bundled in this archive.
Use `Caddyfile.api` for the backend host, and run API/scanner/intelligence/scheduler
there (the native web service is unnecessary when Vercel runs Next.js).
Set backend `WEB_ORIGIN` to the exact Vercel production URL or custom UI domain and
add that domain to Firebase Auth authorized domains. Cookies stay on the UI origin
through Next.js's `/api` proxy. Do not put server credentials in Vercel browser variables.

Vercel's bounded Functions do not run the existing permanent Celery processes. Firebase
Auth alone does not provision PostgreSQL/Redis/workers. A backend hosting destination
is still required. No billing plan upgrade or paid resource has been activated.

Use an operator-managed Linux server with systemd, Node 22+, Python 3.12+, PostgreSQL,
Redis, Caddy, a domain pointing to the server and a real encrypted SMTP relay.
No hosting account is created or charged by these files. Hosting availability/cost is
an operator choice; this document does not promise free always-on infrastructure.

Place the source at `/srv/aegis`, then run as its build owner:

```sh
bash scripts/build-server.sh
```

Create a PostgreSQL database and non-superuser `aegis` role. Restrict PostgreSQL/Redis
to localhost or a private service network. Set passwords through the server's secret
management, not GitHub files. If using a remote database, use its TLS-verified connection
URL. Do not expose ports 3000, 8000, 5432 or 6379 publicly; only HTTPS and required ACME
HTTP validation reach Caddy.

## Runtime secrets

Create system users `aegis-api`, `aegis-web`, `aegis-scanner`, `aegis-intelligence`,
`aegis-notifier` and `aegis-scheduler`. They need read access to `/srv/aegis` but must not own or modify code.
Create `/etc/aegis` as root. Install `production.env.example` as `api.env`, replace every
placeholder and set `WEB_ORIGIN` to the exact HTTPS origin with no trailing slash.
Install copies of `worker.env.example` as `scanner.env`, `intelligence.env` and
`scheduler.env`; configure the same database/queue/origin. **Do not put Firebase,
SMTP or MFA secrets in these worker files.** Create `notifier.env` from
`notifier.env.example` with its own authenticated SMTP credentials; only the
`aegis-notifier` user should read it. Email alerts route to the `notifications`
queue; without the notifier service opt-in notifications will remain pending. Each file must be root-owned,
group-owned by its respective service user, mode 0640. Give `web.env` only:

```text
AEGIS_ENV=production
```

Store the Firebase service-account file at `/etc/aegis/firebase-identity.json`, owned by
root:aegis-api, mode 0640. It must match project `aegis-d034c`. Set the actual public web
apiKey in api.env (the supplied public key is now prefilled in production.env.example).
The complete user-supplied public configuration is retained in
`packages/configuration/firebase.public.json`; only Auth is activated by this integration,
not Storage, Analytics or Firestore. Google/email providers and the actual UI domain must be enabled in
Firebase Authentication. No credentials are included in this repository. A failed
credential/project/revocation check does not create a session.

## Migrate and start

As server administrator, after secret files and database are prepared:

```sh
install -m 644 infrastructure/deployment/aegis@.service /etc/systemd/system/
install -m 644 infrastructure/deployment/aegis-migrate.service /etc/systemd/system/
systemctl daemon-reload
systemctl start aegis-migrate.service
systemctl enable --now aegis@api aegis@web aegis@scanner aegis@intelligence aegis@notifier aegis@scheduler
```

Do not start services if migration fails. Install the supplied Caddyfile, set
`AEGIS_DOMAIN` in Caddy's systemd environment and validate with `caddy validate` before
reloading Caddy. Use the same domain in WEB_ORIGIN and Firebase Authorized domains.
The shared systemd template gives each service its own writable state directory;
only the scheduler writes its beat state. Keep exactly one scheduler instance.

## Verify before granting customer access

- `/api/ready` must return 200 with current database schema and live Redis response.
- Register/verify a real test account, sign in with Firebase, and test logout/reset.
- Promote only your verified operator account via `python -m aegis.cli promote-admin`
  under the API environment; the complete command also requires that account email.
- Open Administration -> Database & connected services. Firebase must say connected,
  both workers must reply and SMTP must respond. These are live checks, not demo values.
- Exercise ownership, scope, full supported assessment, PDF, quotation, approval and
  retest against an explicitly authorized staging asset. Test a second organization.
- Verify encrypted backups and restore into an isolated PostgreSQL database before
  accepting production data. Never use test fixtures against the live database.

Use `journalctl -u aegis@api` and matching service units for failures. Pause assessments
in administration before upgrades; retain encrypted database backups, apply migrations,
restart services and repeat readiness. Do not automatically downgrade a database.

## Verification boundaries

Runtime guard and SMTP tests are executable in tests/test_production_runtime.py.
The complete end-to-end notification queue on the deployed notifier must be tested with an opted-in account, and actual SMTP acceptance checked. Production roles are verified independently; API requires Firebase/MFA/SMTP secrets, notifier only SMTP, scanner/intelligence/scheduler no identity/email secrets.

The full native systemd/Caddy/PostgreSQL/Firebase installation has not been run in the
build environment. No live deployment, DNS setup or cloud authentication is claimed.
Worker code enforces public-IP pinning and authorization; OS/network egress policy and
database privilege separation still require production security review.

Payments are hard-disabled. Quotation acceptance never records a payment.

Official integration references: https://firebase.google.com/docs/admin/setup and
https://firebase.google.com/docs/auth/admin/manage-sessions .
