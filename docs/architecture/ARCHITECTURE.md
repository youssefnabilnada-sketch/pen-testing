# Architecture and decisions

## Process boundaries

- Browser → same-origin Next `/api/*` proxy → FastAPI.
- FastAPI and Celery worker → relational DB. Development integration tests substitute SQLite explicitly.
- FastAPI → Redis for login throttling and Celery enqueue.
- Celery worker → destination policy → pinned socket → normalized observations → transactionally persisted findings/history/report snapshot.
- Browser PDF download → membership check → snapshot rendering, with no HTML fetched during rendering.
- Email tokens → local SMTP/Mailpit. High-entropy token hashes stored; raw token only sent to email.

## Why a modular monolith

A shared backend package reduces deployment complexity. Worker execution is out of process. Splitting findings, AI and reporting into separate network services would create more failure and authorization boundaries without helping this small local core. Separate scanner process with an unprivileged result-only protocol is still a production hardening requirement.

## Data model

Users, sessions, email tokens, organizations, memberships, assets, verification challenges, authorizations with immutable scope JSON, assessment jobs, findings, finding history, report snapshots, remediation requests with quoted scope/task state, conversations, audit events, settings.

A finding is deduplicated by `(asset_id, rule)`. Report snapshots retain the exact findings from that assessment, not mutable current findings. Retests use the same detector suite and exact root scope. A missing observation means only that this root response no longer produced that signal.

Quotation and task data currently share the remediation record. Separate quotation revisions, multiple tasks per request, normalized invoices and attachments are not implemented. Introducing these requires new migrations; it must not overwrite accepted historical scope.

## Authorization

All tenant routes call membership enforcement on the resource's stored organization ID. Viewer cannot mutate. Job launch and finding review require owner/admin/analyst. Engineering transitions require owner/admin/engineer. Quote acceptance requires owner/admin. Platform-admin endpoints explicitly require the server-side superadmin flag. Superadmin does not silently bypass ordinary organization message/report permissions.

## Job safety and recovery

Asset row lock serializes job creation in PostgreSQL (SQLite tests do not validate PostgreSQL locking). Compare-and-swap queued → preparing makes redelivery a no-op. Each phase rechecks authorization expiry/revocation and pause/cancel. One bounded request; target cooldown across tenants uses a Redis origin hash. Worker concurrency one by default; hard time limit 45 seconds. Unsafe or unexpected responses fail closed. Failed/cancelled jobs do not resolve findings. Stale jobs require explicit administrative recovery rather than unbounded retries. A transactional outbox and automated crash reconciliation remain production work.

## Branding and UI

Central CSS variables define dark navy, cyan, violet and severity colors. Brand strings remain in landing/layout/console/report files; a consolidated runtime branding configuration is deferred. Custom accessible HTML controls and CSS replace Tailwind/shadcn; native CSS transitions replace Motion. Three.js is dynamically imported on the landing page only, capped to 30fps and pixel ratio 1.5, disabled for reduced motion. Charts are simple semantic HTML bars/counts, not Recharts. These substitutions are deliberate and recorded, not claims that the requested libraries were installed.

## Future commercial boundaries

BillingAccount, SubscriptionPlan, PricingPolicy, RemediationQuote, InvoiceRecord, PaymentEvent and PaymentProvider interfaces exist in `billing.py`. No SDK, provider route, webhook, card field or payment credential exists. Changing an environment flag cannot activate payments in this build. A future explicitly approved integration would add a provider adapter, signature-verified idempotent event ingestion, separate invoice/payment tables and a durable outbox. Accepted quotes are scope approvals only. Entitlement gates must remain independent of scanner authorization and must not restrict local testing.
