# Historical 0.3 architecture notes

For current identity UI and setup see ../../UPGRADE-0.4.md. Statements below describing
the absence of Firebase UI and uninstalled SDK describe the older 0.3 checkpoint.

# 0.3 integration checkpoint — not a cloud deployment

Existing PostgreSQL/Redis/Celery architecture and local passwords are retained.
Firebase is optional identity infrastructure, NOT an ownership authority or replacement
for the isolated scanner. App Hosting requires Blaze billing; no cloud resources or
paid plan have been activated. https://firebase.google.com/docs/app-hosting/costs
Do not advertise the whole system as free Firebase hosting. A separate API/database/
worker deployment is required. Next.js rewrites must point to a reachable private API;
localhost is not a deployed API. Public hosting is blocked pending TLS, egress firewall,
rate limits, secrets, backup/restore and independent security review.

## Current implementation
- Reusable, tenant-scoped expiring ownership instructions (file, DNS, meta).
- GitHub prefilled file helper (main branch in UI; simple branch names in API),
  root/public directory choice. User reviews/commits; website proof still required.
- Clear consent and disabled-button reason. No production modification capability.
- Optional Firebase server identity adapter: explicitly link an existing verified AEGIS
  account using its current password + CSRF + recently authenticated Firebase ID token.
  Subject and project are uniquely bound; email does not auto-link accounts.
- Firebase login validates signature via Admin SDK, revocation, audience, issuer,
  email_verified and authentication age <=5 minutes. Short AEGIS session: 15 minutes.
  Upstream revocation is checked at login, not continuously; existing local session may
  remain valid for up to 15 minutes. Deactivating the local user takes effect immediately.
- Unlink requires local password and revokes all AEGIS sessions.

## Optional API integration (developer-facing, UI not yet implemented)
Install apps/api/requirements-firebase.txt or use the optional Compose overlay.
Configure FIREBASE_PROJECT_ID, FIREBASE_CREDENTIAL_FILE (outside the repository).
Use a least-privilege service identity allowed to validate account revocation. Never
put a service-account JSON in browser code, NEXT_PUBLIC variables or GitHub.
Use Google's client SDK to obtain a fresh ID token; never paste tokens into logs.
POST /auth/firebase/link {id_token,current_password} with existing cookie + x-csrf-token.
POST /auth/firebase/login {id_token} creates an HttpOnly local cookie and returns CSRF.
DELETE /auth/firebase/link {id_token,current_password} revokes local sessions.
The unlink id_token field is currently required by the input schema but not used.
Swagger: /docs on the API. No frontend Firebase button is claimed in this checkpoint.

Optional local command (after configuring credentials):
`docker compose -f docker-compose.yml -f docker-compose.local-access.yml -f docker-compose.firebase.yml up -d --build`

Live SDK/cloud integration, provider outage/revocation integration, Firebase frontend,
MFA step-up, GitHub App/OAuth install and hosting connectors remain NOT VERIFIED / NOT
IMPLEMENTED respectively. Mocked adapter tests are not evidence of live Firebase success.
Optional SDK dependencies are not yet pinned/audited; production activation is blocked.

## Security tiers and remaining implementation
1. Assessment: verified exact origin + explicit scope. Existing gate retained.
2. Proposed patches: future selected-repository GitHub App, branch only, no direct push.
3. Deployment: future MFA step-up, approved immutable patch digest, staging checks,
   rollback plan, short-lived customer deployment grant. No endpoint currently deploys.
4. Retest: existing full supported-profile regression workflow and tenant reports retained.
Engineer-managed remediation is available now. Do not imply a fix has been applied by
request creation, quote approval, or instructions. DNS/hosting OAuth integrations need
provider-specific review; integrating every provider at once would not be a safe claim.

## GitHub preparation
Upload source only; never upload .env, credentials, database backups, node_modules,
.next or real reports. .env.example is safe configuration documentation, not secrets.
Create a private repository first; review history for secrets before making it public.
No GitHub repository has been created or pushed by this change.
