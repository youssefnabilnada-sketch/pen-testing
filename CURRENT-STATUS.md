# Current engineering state — not a final release

The complete original specification is NOT implemented. This file supersedes earlier
checkpoint handover status; historical test reports remain available for traceability.
No public deployment or payment processing is enabled.

Implemented in this work:
- Durable outbox for on-demand assessments; broker failure retains queued request.
- Recovery of recorded change evidence/rollback/staging details on the remediation page.
- Role-aware customer approval with consent bound to the currently displayed change.
- Retest history, real backend status and report download without manually copied IDs.
- Queued retest cancellation becomes unverified, never verified fixed.
- Quotation, progress and gated completion PDFs with workspace access enforcement.
- API + real owned local HTTP fixture + in-memory Celery customer journey test.

The HTTP fixture still has an unresolved transport finding; the journey verifies that
workflow closure is correctly refused. It does not pretend the fixture is fully secure.
A separate all-supported-checks fixture verifies successful closure and completion PDF.

Unimplemented or incomplete:
- GitHub App / hosting / DNS OAuth connectors and reviewed automated patch delivery.
- Generic sensitive-action step-up remains incomplete. Profile, password change, account deactivation and explicit ownership transfer are implemented with password/factor confirmation; production concurrency acceptance is outstanding.
- Team invitations, role changes and removal are now implemented; PostgreSQL concurrency and real inbox acceptance remain unverified.
- Binary/PDF/image attachments and email notification preferences remain incomplete. Bounded text evidence, tenant/private-file controls, personal in-app preferences and per-user read receipts are implemented.
- Multi-path assessment scopes and broader detector profiles remain incomplete. Recurring assessments now support enforced daily UTC windows, scheduler deferral and transport-time authorization rechecks.
- Configured external/local AI providers, expanded vulnerability source coverage.
- Full operations console, production hardening and deployment integration.

Blocked/unexecuted verification:
- Real Firebase sign-in, Google consent and provider email delivery (server credentials
  are not configured here; never send credentials through chat).
- Docker/PostgreSQL/Redis complete deployment, backup/restore, concurrency acceptance.
- Browser desktop/mobile/keyboard/accessibility and independent security review.

Online deployment is now the primary delivery target; see DEPLOY.md. Added live connection diagnostics, migration checks, encrypted SMTP, production runtime safety gates, native systemd/Caddy deployment files and a Vercel API-origin build guard. The native deployment and actual cloud Firebase connection have NOT been executed.

Keep the existing installation and private backups. Current changes require migration 009_profile; it adds evidence attachments, personal notification state and optional profile names after the MFA migration. Existing deployment remains localhost-only. Do not run
`docker compose down -v`. This work is not a recommendation to expose the scanner publicly.

Run backend: PYTHONPATH=apps/api python -m pytest tests -q --cov=aegis
Run frontend: npm --prefix apps/web test; npm --prefix apps/web run typecheck;
npm --prefix apps/web run build
Evidence: docs/testing/backend-current.log, coverage-current.json and RESULTS-CURRENT.md.

Latest work: team invitations/roles/removal and account email links; executed evidence in docs/testing/TEAM-RESULTS.md. No new customer setup information is needed to continue coding. Online hosting/credentials remain separate unexecuted deployment prerequisites.

Latest verification: support module integrated; see docs/testing/SUPPORT-RESULTS.md (112 backend passes, 28 frontend passes). Binary attachments and the remaining original-spec gaps are not complete.

Latest internal verification: optional authenticator MFA and Firebase identity-change factor checks; see docs/testing/MFA-RESULTS.md. User explicitly requested no interim package delivery. Whole-product final acceptance is not complete.

Latest internal work: support/remediation text attachments, personal notifications, profile/password/session controls, guarded deactivation and explicit organization ownership transfer. See docs/testing/LIFECYCLE-RESULTS.md. No interim source package is being presented as final.

Permitted monitoring windows and live transport authorization rechecks: see docs/testing/WINDOWS-RESULTS.md. This extends the single-root-response profile; it does not add crawling, exploitation or unapproved destinations.

Latest executed regression: 130 backend passes, 1 default-suite skip; separate real Redis 2 passes; 39 frontend passes; Next production build and TypeScript pass. Evidence: docs/testing/WINDOWS-RESULTS.md. No full-product or deployment acceptance is implied.

26 October 2026 integration work:
- Code-owned CSP base-uri and cookie SameSite candidates, version/fixture/admin gates,
  disable action, first-directive CSP parsing and conservative unsupported-policy retesting.
- Superadmin operational record pages and counters; stale recovery now updates dependent
  retests/schedules and prevents terminal-job resumption at worker checkpoints.
- Server-paginated finding search/sort/history with explicit role controls; retest navigation
  no longer depends on the first 100 findings being loaded.
- Optional chat-completions-compatible effort estimator, private environment configuration,
  constrained outputs, public HTTPS transport and global cooldown. Deterministic explanations
  remain the default. General AI freeform remediation, local model integration and live provider
  acceptance remain incomplete; see docs/architecture/OPTIONAL-AI.md.

These changes do not fulfill the remaining full-product requirements. Firebase is identity
integration only, not a Firestore replacement for PostgreSQL. Vercel frontend deployment
still requires a separately running API/worker/database architecture. Real cloud integration,
PostgreSQL concurrency, browser acceptance and independent security review remain blocked
or unexecuted. No final release or interim download is being delivered.

Latest aggregate: 163 backend passes / 1 default-suite skip, 2 separately executed real
Redis passes, 45 frontend passes, 91.5593% measured backend statement coverage, successful
Next build (console 130kB first-load JS). See docs/testing/INTEGRATED-RESULTS.md. This
supersedes earlier totals without implying completion of the full requested product.

Latest remediation workflow verification: severity-based bulk requests, consistent individual
request eligibility, idempotent review tickets, server-side remediation pagination/status filters
and workspace refresh sequencing. 166 backend passes / 1 skip; 49 frontend passes; build/static
checks pass. Measured statement coverage 91.6001%. See docs/testing/SELECTION-RESULTS.md.
This does not change the outstanding full-product and deployment blockers above.

Shared scope validator now enforces identical method, root path, exact origin, integer request budget and timeout in manual/scheduled/retest enqueue and worker checkpoints. Focused safety tests: 21 passes; full regression evidence in docs/testing/scope-full.xml/log. Multi-path assessment remains incomplete.

PHP CPE stable-version inventory range matching added; 30 focused inventory/intelligence
tests passed. Vendor builds and unsupported version semantics stay unknown. No claim of
live PHP advisory ingestion or runtime vulnerability detection. See docs/testing/PHP-INVENTORY.md.

Consolidated regression after scope/queue/PHP matching changes: 188 backend tests passed,
1 skipped, 93.83s; 49 frontend tests passed, 6.73s. Raw evidence consolidated-regression.xml/log
and consolidated-frontend.log. No new feature implementation or cloud/browser acceptance is
implied by this regression run; remaining requirements above are still incomplete.

PNG evidence implementation added with bounded decoding/re-encoding and metadata stripping.
8 focused tests passed; new PNG route/browser end-to-end and full regression remain outstanding.
This feature is not yet marked complete. See docs/testing/PNG-EVIDENCE.md.

PNG follow-up verification completed: API roundtrip and tenant rejection, component upload,
full backend 194 passes/1 skip, frontend 50 passes, Next build pass. Direct pinned backend
dependency audit found no known vulnerabilities; no transitive audit claim. See PNG-EVIDENCE.md.
Browser/public deployment and the remaining original requirements are still not complete.
