# AEGIS v1 — Public launch acceptance record (2026-10-31)

**Decision: NO-GO for open customer registration until live gates are evidenced.**
The candidate is based on release/aegis-v1-final, not a new product. No changes to Oracle/Docker/Firebase/production secrets, database migrations or public registration settings.

## What engineering completed in the candidate
- Platform-specific Arabic/English ownership instructions covering WordPress, Shopify, Wix, Squarespace, Cloudflare, Vercel, Netlify, cPanel/Plesk, GitHub, Google Search Console and custom sites.
- Playable animated tutorials embedded in SmartVerify for the chosen provider and file/DNS/meta proof method, including play, pause, timeline, and replay.
- These are animated guides, **not** actual MP4 recordings or unimplemented provider OAuth connectors.
- Safer login HTTP error messages distinguish invalid credentials from gateway/service failure without displaying secret-bearing backend responses.
- Existing exact-origin ownership proof and separate scoped assessment authorization, GitHub helpers, Cloudflare assistance, and WordPress remain unchanged.

## Automatically verifiable gates
- [ ] CI green on exact candidate SHA: frontend tests, TypeScript, build, backend, PostgreSQL/Redis, WordPress, native runtime, browser desktop/mobile and repository history.
- [ ] Isolated Vercel Preview READY for the same SHA. Protected preview is not proof of production sign-in.
- [ ] Read-only official-domain statuses observed without credentials by scripts/launch_readonly_probe.py. Status observations alone do not establish production correctness.
- [ ] No browser simulation can silently authorize an assessment.

## Required live operator evidence before public registration
1. Correct official production Vercel SHA, verified domain, API endpoint and server-only gateway configuration. Never display the production gateway key.
2. Read-only Oracle API, PostgreSQL, Redis, workers and Caddy readiness; inspect proxy access-control policy without restarting services.
3. Approved pilot account: email verification, real official-domain browser login, Firebase Google authorized domain, Brevo inbox delivery, HttpOnly/Secure/SameSite session, CSRF denial, logout, account recovery on the pilot only and cross-tenant access denial.
4. Ownership on a disposable owned site with file, DNS and meta (and WordPress/Cloudflare as appropriate); confirm ownership does not itself start a scan.
5. Separate authorized bounded assessment, PDF report, remediation workflow, FastFix PR review on disposable repository, staging and retest; never automatically change customer production.
6. Scanner-egress/network segregation, nonspoofable source rate limits, encrypted recurring backups with a disposable restore drill, TLS/alerts, monitoring, privacy, retention and incident procedures.
7. Approve merge to release, controlled deployment with verified rollback, then and only then opt in public registration. Payments, unapproved remote AI and automatic production changes remain disabled.

## Why a public launch is not yet certified
- The user observed Service unavailable during pilot sign-in. The failing URL and HTTP response status have not been established from an authorized real browser.
- Current automated CI/browser fixtures are isolated, not a replacement for the Oracle-hosted production service.
- The pilot operator retains responsibility for SSH-side inspection, authenticated browser acceptance, network/backup drills, and release authorization.

## Safe operating procedure
Use docs/deployment/AEGIS-V1-OPERATOR-RUNBOOK.md for the latest reviewed Oracle sequence. Do not paste tokens, secrets, session cookies or passwords into chat or CI logs. Do not run destructive Docker volume/database commands. Do not redeploy Oracle for UI-only changes.