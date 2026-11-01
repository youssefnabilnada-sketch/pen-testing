# AEGIS v1 — production gateway enablement and release acceptance

**Status: BLOCKED / production traffic intentionally closed.** This document describes the final production gateway path; it does not authorize changing live infrastructure or enabling public registration.

## Verified source and release
- Working release branch: `release/aegis-v1-final`.
- GitHub CI must be green **on the final exact SHA after gateway code and tests**; older green SHA is not current acceptance evidence.
- Existing Vercel project: `pen-testing` (Next.js root `apps/web`); public intended domain: `https://aegis-pentest-eg.vercel.app`.
- Existing OCI API HTTPS origin: `https://aegis-pentest-eg-api.duckdns.org`.
- Oracle API, PostgreSQL, Redis and workers were previously staged under guarded rollout; this does **not** establish production signoff.

## Fail-closed Next.js production gate (code shipped on release branch)
- Both `/api/auth/*` and non-health `/api/*` refuse production traffic with HTTP 503 unless **Production-only** server environment contains:
  - `AEGIS_PRODUCTION_GATEWAY_ENABLED=true`
  - `AEGIS_PRODUCTION_GATEWAY_KEY=<random strong URL-safe value, minimum 48 characters>`.
- Neither key is `NEXT_PUBLIC_*`; never write it to GitHub, logs, screenshots, query parameters, or browser storage. Preview keys must **never** authorize production. The header used between Next.js and existing Caddy gateway is `X-AEGIS-Preview-Gateway` (legacy wire name; the value is the production-only key).
- Mutating requests require a browser `Origin` **exactly** equal to the effective Next.js site origin. The proxy forwards only allowed account cookie / selected headers and rejects redirects and unbounded bodies.
- The API `/health` read path is intentionally allowed without this key. The separate Oracle public `/health` and Firebase web-config read endpoint are not proof that account writes work.

## Required independent configuration and verification BEFORE enabling
1. Review production-origin Caddy policy with the service operator. Caddy must validate the strong **production-only** key for specifically enumerated proxied API routes/methods, reject missing, wrong and preview keys, and keep direct public mutations at 503. Verify unauthorized requests are rejected **before** enabling Vercel's production flag.
2. Set canonical `WEB_ORIGIN=https://aegis-pentest-eg.vercel.app` in API runtime and precise allowed Firebase Auth domain. Preserve tenant auth, CSRF and request rate limits; no wildcard CORS, suffix matching, or trusting browser-provided forwarded-IP headers.
3. Set the gateway secret privately in OCI Caddy and in **Vercel Production only**. Confirm the same key without printing it. Verify Vercel production `API_INTERNAL_URL` is the correct HTTPS API origin. Preview variables cannot enable this production gate.
4. Deploy exact final approved source into existing `pen-testing` Production target only after passing review, Vercel settings/build and CI gate. Exercise registration, verification email receipt (Brevo), login/Firebase, host-only HttpOnly Secure SameSite cookie, session persistence, logout, CSRF, role/tenant negative cases, and fresh authorized ownership + scoped scan.
5. Check deterministic report rendering, bounded request cancellation, worker/queue status, FastFix customer proposal/approval + rollback/retest, API scope constraints, backups/restore, monitoring, alerts and emergency cut-off. Document all remaining unsupported product functionality; do not advertise anything unverified.
6. Keep billing, auto production changes, and unsanctioned scheduler OFF. Only explicitly approve public registration after the above acceptance evidence is archived and security/UX review accepted.

## Safe shutdown and rollback
- To immediately close Next.js business/auth access, remove the production opt-in or key in Vercel Production and redeploy; Caddy must independently reject requests if the matching secret is missing or disabled.
- Caddy's emergency block must not rely on a browser-visible flag. Backups and a database-safe rollback must be verified before customer release.
- Never expose the public auth POST or business API without verified identity, scope and approved gateway; a READY deployment by itself is not an acceptance test.
- Production never depends on Vercel's broken **branch-scoped Preview** variable path; see GitHub issue #13. This does not eliminate the independent OCI configuration or live browser tests.

## Existing evidence and known gaps
- Automated CI and isolated browser/API tests prove only the tested commit in an isolated fixture environment. Live OCI/Vercel/Firebase/Brevo browser integration has not been accepted.
- Current production web deploy was historically ERROR due Vercel's Python entrypoint detection on old `main` commit. The existing project now builds Next.js previews successfully; production release must still be tested explicitly.
