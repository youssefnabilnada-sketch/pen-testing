# Intelligence, monitoring and full supported-profile retesting — 0.2

## Implemented trust boundaries

The intelligence worker retrieves only fixed HTTPS endpoints: CISA KEV, NVD CVE API, GitHub reviewed advisories, and OSV lookups for known GHSA identifiers. Transport resolves and pins public IPs, verifies TLS hostnames, disallows redirects/proxies, bounds payload size and duration, and rejects unexpected pagination destinations. No target inventory is sent to feeds. Source references are displayed as links, never automatically executed or fetched as instructions.

CISA uses its full catalog. NVD/GitHub start at the last 24 hours and then use incremental checkpoints. OSV refreshes up to 25 known GHSA identifiers per cycle; it is not a complete historical OSV import. Failed/incomplete batches roll back records and retain the previous cursor, retry with bounded backoff, and expose last success/error. Configure each source interval from 6 to 12 hours. Celery beat must actually be running; this application does not keep updating after its services stop.

References: https://nvd.nist.gov/developers/vulnerabilities ; https://www.cisa.gov/known-exploited-vulnerabilities-catalog ; https://docs.github.com/en/rest/security-advisories/global-advisories ; https://google.github.io/osv.dev/api/ . Live transport could not be validated in this environment; see testing/live-feed-check.txt. Schema tests use fictional advisories.

Advisory aliases deduplicate CVE/GHSA identities; conflicting alias graphs stop ingestion for review. Content hashes identify immutable source revisions. Changes invalidate knowledge approval. Only current approved revisions enter lexical retrieval and deterministic guidance. This is evidence-grounded fallback synthesis, not an active LLM/RAG provider or model-weight retraining. No advisory can authorize a target or activate a detector. The code-owned Referrer-Policy candidate requires fixed fixture validation and explicit administrator approval.

## Inventory and tenant impact

Authorized owner-declared inventories and exact requirements/npm lock manifests are parsed as data. Scripts and dependency downloads never run. Supported stable version ranges match locally; missing/unsupported/conflicting semantics stay potential. An exact declared-version match is not confirmed deployed exploitability and does not create a scanner finding. Tenant-scoped impact records and deduplicated notifications are separate from global advisories. Notifications are currently workspace-level, including their read state.

## Monitoring

Daily, weekly, every-30-days and opted-in relevant-advisory triggers share the exact-origin/root-only profile. Customer consent lasts 1–90 days. The scheduler checks current authorization, verification, pause, scope and active jobs. Explicit opt-in permits rechecking a still-published ownership challenge when proof expires; expired consent is never renewed automatically. Blocked schedules emit deduplicated notifications. A persistent outbox retries broker dispatch; compare-and-swap job claims prevent duplicate network execution. Original on-demand job submission still uses the earlier direct dispatch path.

## Remediation regression gate

An engineer records authorized change evidence, rollback planning and staging validation. This records an externally applied change; the platform has no source-repository or deployment access. Customer Owner/Admin approval selects valid authorization and queues the complete applicable profile, not only the original check. The baseline includes all historical asset findings, newly approved rules execute, and relevant inventory advisories are evaluated separately.

The immutable comparison classifies resolved, unresolved, new and unverified observations. Absence of a cookie is insufficient to prove its flags fixed. Unsupported checks stay unverified. Still-detected original findings reopen and record history. Failed/cancelled jobs never verify a fix. The original may pass while regressions remain: task closure additionally blocks on unresolved/new/unverified results and unverified advisory runtime impact. Reports state limitations and do not certify overall security.

## Deliberate remaining gaps

- Direct CVE.org/vendor/OWASP/research ingestion adapters and complete historical backfills.
- Active external/local AI provider, vector retrieval, provider reliability/injection tests and automatic factual validation of generated patches.
- Authorized repository connections, patch generation/testing/approval and production deployment: the patch endpoint explicitly rejects absent access.
- Advisory-specific runtime detectors; inventory matching alone cannot verify a vulnerability or a fix.
- Arbitrary paths, crawls, authenticated checks, calendar windows, broad TLS analysis and comprehensive penetration testing.
- Real PostgreSQL/Redis/Celery-beat integration, concurrency stress, live feed connectivity, full browser journey and visual testing remain release blockers.
- Long-term knowledge retention, deletion, scale/pagination UX, per-user notifications and email alert preferences.

Payments remain disabled and are independent of every workflow.
