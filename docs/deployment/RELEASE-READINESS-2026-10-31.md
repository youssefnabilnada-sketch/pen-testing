# AEGIS Security Cloud — verified release-readiness register
**Updated:** 2026-10-31 (UTC+03 / Cairo). **Decision: NO-GO for public customer launch.**
This is a source-linked deployment handoff, not a security certification or a claim that missing modules have been completed.

## Known running environments (operator evidence vs CI)

| Component / evidence | State | What this proves | What it does not prove |
|---|---|---|---|
| Oracle ARM64: PostgreSQL, Redis, FastAPI, Caddy, scanner/intelligence/notifier | **PASS, operator acceptance** | Read-only integration probe `AEGIS_ACCEPTANCE_READONLY_PASS`; PostgreSQL at migration `017_evidence_legal_holds`; 52 public-schema tables; API `/ready` | Recovery after reboot, correct worker network segregation, high load, production security review |
| Oracle local account + Gmail plus-alias | **PASS, operator acceptance** | `AEGIS_LOCAL_ACCOUNT_ACCEPTANCE_PASS`: real email delivered through Brevo, verify token, login, role denial, CSRF, logout/session revocation, temporary-account deactivation | Browser/Vercel cookie persistence, Firebase browser login, Google consent or real customers |
| Oracle Caddy HTTPS | **STAGED / PROTECTED** | `GET /health` returns 200; `GET /auth/firebase/config` returns 200; unauthorized `GET /auth/me` returns 401. All public auth POST, other business endpoints and OpenAPI remain 503 | Customer usage or public registration |
| Vercel frontend | **PREVIEW READY** | User viewed Astra landing/workspace; Preview deployments from UX commit `54cf1c7`, error-copy commit `730beda` are READY | Production deployment, browser integration or complete product |
| CI for UX | **PASS** | GitHub Actions [41131714586](https://github.com/youssefnabilnada-sketch/pen-testing/actions/runs/41131714586), ten jobs passed (fixtures, controlled browser smoke and backend) | Live Google, email inboxes, provider APIs or third-party audits |
| CI for exact preview Origin | **PASS** | GitHub Actions [41137760875](https://github.com/youssefnabilnada-sketch/pen-testing/actions/runs/41137760875), ten jobs passed | Patch installed on running Oracle API |
| Vercel Production | **NOT DEPLOYED** | Production last listed as ERROR; latest READY deployments have target Preview | Official customer website |
| Recurring scheduler and billing | **OFF** | Scheduler not running per OCI acceptance, payments disabled by config | Recurring customer monitoring or billing |

## Release blocking work — in strict dependency order

### A. Protected browser-auth acceptance (must pass before open registration)
- [x] Real local SMTP delivery, email token verification, session + CSRF and deactivation.
- [x] Public Firebase web config available behind HTTPS.
- [x] Existing backend accepts only canonical `WEB_ORIGIN`; strict preview-only opt-in patch authored on [PR #6](https://github.com/youssefnabilnada-sketch/pen-testing/pull/6).
- [ ] Review integrated staging code on [PR #7](https://github.com/youssefnabilnada-sketch/pen-testing/pull/7): Next.js server-only auth proxy, cookie/CSRF propagation, exact preview Origin. Require passing CI and protected Preview.
- [ ] Verify a **single stable** protected Vercel Preview domain is in Firebase Authentication Authorized Domains; provider has Google sign-in enabled.
- [ ] Operator installs the reviewed API patch on Oracle **without resetting PostgreSQL, Redis or secrets**; sets exact `WEB_PREVIEW_ORIGIN` and opt-in flag only for a short, gated pilot.
- [ ] Operator configures one strong random preview gateway secret **locally** in Caddy systemd environment and Vercel Preview server environment; never put secret into GitHub, URL query or public `NEXT_PUBLIC_*` variables.
- [ ] Only explicit auth paths/methods may pass Caddy when validated server-side secret matches. Every direct public request must remain 503; health and Firebase config stay read-only.
- [ ] Test real Vercel browser: register one fresh authorized test account, receive verify email, sign in, `Set-Cookie` host-only/HttpOnly/Secure/SameSite, `/auth/me` authorized, CSRF write denied/allowed as appropriate, sign out, no cross-account/tenant access, Google identity create/link vs sign in, disabled/revoked sessions.
- [ ] Test Vercel Preview protection and rollback. Remove preview secret and opt-in, retain blocked public routes once testing concludes.

### B. Security/operations before public access
- [ ] Fix trusted-proxy/real-source rate limiting: current API rate limiting by `request.client.host` may group many Vercel users behind one egress address. Do not trust arbitrary `X-Forwarded-For` from the public internet.
- [ ] Keep scanner egress segregated from DB and Redis secrets, enforce outbound destination restrictions in actual OCI networking, and independently test SSRF/DNS rebinding/redirect/IPv4+IPv6 protections.
- [ ] Test PostgreSQL concurrency and tenant ownership/authorization across ALL cross-org routes. Include MFA/admin/role/agency boundaries.
- [ ] Complete encrypted backup scheduling and a **disposable restore** drill. Review storage, legal hold and retention without destroying production data.
- [ ] Review observability/alerts, restart durability, resource quotas, p95 response time, queue backpressure, TLS expiry, incident response and privacy/support policies.
- [ ] Dependency and repository-secret audit; rotate any key ever pasted into chat, publicly shared screenshots, or committed history. Do not echo or store credentials in reports.

### C. Complete original product and UX specification (not a launch claim)
- [ ] Complete specialist Arabic UI/server explanations, RTL/keyboard/mobile and reduced-motion/WebGL fallback visual checks on real devices.
- [ ] Fully implement and verify SmartVerify/ownership proofs and multi-path authorized discovery; confirm precise scope controls for website/API profiles and unsupported-check transparency.
- [ ] Complete and test FastFix GitHub/hosting integration, staging evidence, human approvals and tested rollback/retest; **never automatically edit customer production**.
- [ ] Validate Launch Guard, website/domain/SSL monitoring, agency branding/white-label reports, notifications/intelligence feed freshness, and technical/executive PDF reporting with real authorized fixtures.
- [ ] Validate support, invitations, account recovery, admin operations, audit/retention and privacy processes end to end. Distinguish implemented local modules from production-accepted functions.
- [ ] Optional remote AI provider remains disabled until independently approved/validated with cost and injection controls; **payments remain disabled** until separately authorized.

### D. Final production release (after A–C minimum approved scope)
- [ ] Reconcile Astra UX branch and reviewed Oracle operations into one tested release candidate; no force-push/reset or unreviewed merge.
- [ ] Re-run all 10 GitHub CI jobs on **exact release SHA**, verify customer browser journey on protected Preview, security gate and backup/rollback.
- [ ] Production domain `aegis-pentest-eg.vercel.app`: verified official Vercel deployment + authenticated API routes + exact canonical `WEB_ORIGIN`/Firebase Authorized Domains.
- [ ] Post-deploy smoke checks, log/alert review, customer scope documentation and rollback rehearsal.
- [ ] **Only after all required checks pass:** explicitly approve opening customer sign-in/assessments on the agreed scope. Do not turn on scheduler or billing by default.

## Branch ownership and safety

- UX: `feature/aegis-ultimate-ux-redesign` at `54cf1c7` (Astra still independently developing).
- Oracle ops: `deploy/oracle-always-free-prep-20261028` at `f86eeabe` ([Draft PR #2](https://github.com/youssefnabilnada-sketch/pen-testing/pull/2)).
- Origin patch: `fix/aegis-exact-preview-origin-20261031` ([Draft PR #6](https://github.com/youssefnabilnada-sketch/pen-testing/pull/6)).
- Integrated release work: `release/aegis-secure-integration-20261031` ([Draft PR #7](https://github.com/youssefnabilnada-sketch/pen-testing/pull/7)).
- **Never** merge this integration branch into production or flip public Caddy access before authenticated browser acceptance and safety review.
