# AEGIS 0.4 — Firebase identity UI checkpoint

This checkpoint adds Firebase identity UI to 0.3. It is not the final complete SaaS,
not a public deployment, and not proof that live Google/Firebase integration succeeds.
All earlier assessment, authorization, intelligence and remediation limitations remain.

## Added
- Google popup and email/password Firebase flows using the official SDK loaded on demand.
- Explicit new-account registration with verified recent identity and an AEGIS recovery
  password. No automatic merging of accounts with equal email addresses.
- Account security page for linking/unlinking; current AEGIS password and CSRF required.
- Firebase email verification and reset flows. Firebase password and AEGIS recovery
  password are separate. Use the original local reset flow to reset AEGIS credentials.
- In-memory Firebase session, token exchange for HttpOnly AEGIS cookie, SDK sign-out
  after exchange (including failures). AEGIS session expires after 15 minutes.
- Public configuration served at runtime; no service-account data exposed to browsers.
- Existing local sign-in remains available when Firebase is disabled or unavailable.

## What you already configured
Project ID from the supplied screenshot: aegis-d034c.
User reports enabling Google, Email/Password and authorizing localhost; no live login
was executed by us. Spark was visible in the supplied console screenshot.

## Enable locally after backup
Keep .env, old source, and a database backup. Never run `docker compose down -v`.
Follow UPGRADE-0.3.md backup instructions. There is no new migration beyond 003_firebase.
The optional feature is disabled by default and does not require credentials to run tests.

In your local .env, set these values from Firebase web configuration:
```
FIREBASE_PROJECT_ID=aegis-d034c
FIREBASE_WEB_API_KEY=<public apiKey from Firebase web configuration>
FIREBASE_WEB_APP_ID=<public appId from Firebase web configuration>
FIREBASE_CREDENTIAL_FILE=C:/private/aegis-firebase-identity.json
```
The file path is an example, not an existing credential. Server-side Firebase Admin
credentials with permission to read Auth users are needed for revocation checks. Keep
that credential outside the repository and do not send it through chat. Prefer managed
workload identity for a future hosted API. No service-account key has been generated.
The optional Compose overlay enables identity only on the API and mounts credentials
only there; workers never receive Firebase credentials.

PowerShell, one command per line:
```
docker compose -f docker-compose.yml -f docker-compose.local-access.yml -f docker-compose.firebase.yml build
docker compose -f docker-compose.yml -f docker-compose.local-access.yml -f docker-compose.firebase.yml run --rm migrate
docker compose -f docker-compose.yml -f docker-compose.local-access.yml -f docker-compose.firebase.yml up -d
```
Without configured credentials, use only docker-compose.yml + local-access overlay;
local authentication remains functional and Firebase controls stay hidden.

## Test on your machine when configured
1. Existing customer: local sign-in → Account security → enter current AEGIS password →
   Link Google identity. Sign out, then Continue with Google. Verify same workspace/data.
2. New customer: Create a new AEGIS account → choose recovery password → Google, or
   Firebase email/password. For email, follow verification email and repeat the action.
3. Confirm another account cannot access the first customer's assets or reports.
4. Cancel popup; deny consent; disable network. Confirm useful error and no session.
5. Unlink with AEGIS password. All AEGIS sessions should end; local recovery login works.
6. Test desktop/mobile and popup blockers. Google consent delivery and provider email
   have not been tested here. Do not mark live integration complete before these pass.

## Security boundaries
Firebase login does not verify domains or authorize assessments/deployments. Verification,
explicit scope, expiry, SSRF controls, no-payment flags and retest requirements are retained.
Upstream revocation checked on Firebase token exchange; current local session can remain
valid up to 15 minutes. Local deactivation takes effect on each authenticated request.
No automatic production patches, hosting OAuth connectors or MFA step-up are implemented.
Firebase App Hosting requires Blaze; no billing enabled or cloud resources deployed.

## Reproduce automated checks
Backend: install requirements-dev.txt + requirements-firebase.txt, then
`PYTHONPATH=apps/api pytest tests -q --cov=aegis` (PowerShell: set $env:PYTHONPATH first).
Frontend: `npm --prefix apps/web ci`, `npm --prefix apps/web test`,
`npm --prefix apps/web run typecheck`, `npm --prefix apps/web run build`.
Full evidence: docs/testing/RESULTS-0.4.md and accompanying audit/test files.
