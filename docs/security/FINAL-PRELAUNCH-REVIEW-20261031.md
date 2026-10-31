# AEGIS v1 — prelaunch security and FastFix review (31 October 2026)

**Decision: NO-GO for unrestricted public registration as of this review.** This is a targeted source-and-evidence review, not an independent penetration test, production credential audit, or proof of a live recoverable backup. Existing production is unchanged by this review.

## Reviewed evidence
- Production source at release/aegis-v1-final \`aa2f8c39c2506cf1b38f7574a24e2766dca0294e\`; registration/backup candidate is draft PR #25 and requires fresh CI for the exact approved head.
- Latest prior production gateway read-only smoke and guest desktop/mobile browser workflow succeeded on the released SHA: GitHub Actions run 41238706099. Existing live production domain is https://aegis-pentest-eg.vercel.app.
- Operator-reported real registration/Brevo, owned website verification, bounded assessment and generated report are valuable functional evidence, but independently reproducible logs for **two-tenant negative cases and backup restore** were not provided. Do not infer coverage or launch approval.
- Existing CI covers PostgreSQL/Redis, Firebase fixtures, WordPress fixtures, scoped assessment and GitHub proposal behavior; it does not substitute for current customer identity, offsite restore or independent security acceptance.

## Audit areas

| Area | Source/evidence | Final result and remaining gate |
| --- | --- | --- |
| Public auth gate | main.py and firebase_identity.py require exact AEGIS_PUBLIC_REGISTRATION_ENABLED=true in production; Next auth/business proxy checks private Vercel-to-Caddy production gateway | FAIL CLOSED pending backup/security signoff. Draft PR makes signup UI report the real backend gate; it must not imply launch is open until API says so |
| Session and CSRF | auth.py hashes session tokens, requires CSRF for authenticated mutations, sets HttpOnly Secure SameSite=Strict cookies; web proxy enforces exact Origin for mutating requests | Source guard exists; live stolen-session, role-change, invitation, session expiry and cross-tenant negative matrix remain unverified |
| Scanner SSRF/authorization | safety.py rejects internal/special addresses, pins a verified DNS answer, rejects redirects; scoped authorization and bounded GET | Code control exists; production egress firewall segregation and independent DNS/IPv6/rebinding review are NOT certified |
| FastFix guidance | fastfix.py verifies tenant/asset/assessment association and returns deterministic, explicitly nonexecuting guidance | Guidance is suitable only as guidance, NOT an approved universal AI automatic fixer |
| Reviewed GitHub patch | repositories.py permits existing vercel.json or netlify.toml \`header.nosniff\` proposals after accepted remediation, stale finding check, repo OAuth, MFA, exact diff; backup and rollback-preview in autofix_recovery.py | SOURCE REVIEW PASS for limited proposal contract; LIVE provider repo+staging+rollback/retest evidence is missing; no customer production patch automation |
| Staging | staging_evidence.py checks supported bounded response observations and keeps deployment_revision_verified=false | Do not declare that a commit shipped or a finding was resolved without separately verified deployed revision, application compatibility and authorized retest |
| Database recovery | CI synthetic dump/restore; scripts/oci-disposable-restore-drill.sh on Oracle; draft opt-in encrypted backup script | CRITICAL OPEN: no observed encrypted offsite production backup and isolated restore of that ciphertext, plus key/config recovery |
| Production browser policy | Next next.config.ts: nosniff, DENY framing, Referrer and Permissions headers; Caddy has HSTS | Strict, tested CSP and authenticated-browser security acceptance still open; do not add breaking policy without compatibility review |
| Privacy and isolation | tenant membership checks, internal role checks and test coverage | Need live test of two independent customer organizations, private report/attachment access, retention/deletion, audit and incident processes |
| Availability | workers, Redis, readiness, protected gateway and notifier active in operator output | Worker concurrency, queue overload, recovery, monitoring/alerts and failure-mode tests needed; recurring scheduler remains off |
| Payments/AI | production runtime rejects billing and public AI enablement for this release | Keep disabled. Do not advertise unavailable universal autonomous remediation or a full pentest |

## Safe prerequisites before GO
1. Verify latest exact release candidate has ALL required CI jobs green (backend/web/integrated Postgres/Redis, native, WordPress, browser, history and release evidence). Resolve skips and any failed runs. Review draft changes prior to merge.
2. Run on the owned Oracle host: protected connections check; disposable restore rehearsal; **encrypted production backup and offsite decryption/restore to an isolated host**; preserve separate recoverable keys and service config. Record evidence without sensitive data.
3. Exercise real authenticated browser onboarding as two different organizations: local email + Brevo verification/reset, Google identity, session, sign-out; create owned assets with fresh explicit consent; verify scoped scan/report; negative tenant and privilege tests. Do not use third-party websites or customer data as fixtures.
4. Validate FastFix only for supported approved change paths: authorized test repo, exact finding snapshot, MFA, draft PR, staging actual deployed revision/behavior, safe rollback and new authorized retest. Unsupported platforms remain engineering handoff.
5. Independent security/privacy review of production network egress, SSRF protections, CSP, account abuse protection, backups, retention, incident response and monitoring; log signoff.
6. Only after all required approvals, roll out the new API and UI with code-pinned releases, then operator may set AEGIS_PUBLIC_REGISTRATION_ENABLED=true in the protected Oracle API environment and restart the API. Never disable the separate Vercel/Caddy gateway or CSRF protections. Verify status/registration again and keep a rollback plan.

## Immediate rollback of signup
Set AEGIS_PUBLIC_REGISTRATION_ENABLED=false (or remove it) in the root-protected Oracle API env and restart **only the API** with systemd after confirming the correct service and source. Recheck that public registration is refused. Do not expose direct Oracle API writes or weaken the Vercel/Caddy gateway. Stop scans separately via the admin emergency control if operational risk warrants it.

**Not approved:** payment activation, GitHub auto-merge, automatic customer production changes, automatic recurring scanner without user authorization, changing production DNS/aliases, or claiming 100% security.
