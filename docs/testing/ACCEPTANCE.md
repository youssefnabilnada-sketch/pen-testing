# Incremental acceptance gates

1. Foundation: registration rejects weak passwords; Argon2 authentication; hashed expiring sessions; CSRF protection; verified email required to create an organization; membership required for every tenant resource. Unauthorized and cross-tenant reads/writes must return 403/404. Run backend foundation suite before dependent features.
2. Interface: real API-backed forms, empty/error states, responsive navigation and reduced-motion fallback. Typecheck/build before integration. Browser verification is a separate gate.
3. Authorization: exact canonical origin, expiring challenges and authorization, explicit root-only scope, no implicit subdomains; every destination resolved and validated then connected by pinned IP. Reject redirects, private/mixed DNS answers, URL credentials, non-standard ports and ambiguous paths. Local fixture exception only in explicit server-controlled fixture mode.
4. Assessment: persisted queued job dispatched to worker; idempotent claim; cancellation checked between bounded requests; actual header/cookie/TLS observations only. No bodies persisted. Failures must not imply clean findings. No resolution on incomplete scans.
5. Results: deduplication by asset/rule, history and re-open on recurrence; report downloads require membership. Deterministic summaries cannot execute actions. No provider credentials required.
6. Remediation: preliminary estimate -> admin quotation -> customer acceptance -> engineer task -> retest. No acceptance implies payment. Illegal transitions rejected.
7. Operations: admin-only pause, audited changes, real queue connectivity and worker status; no placeholder healthy values.
8. Release: full Compose E2E, browser accessibility/mobile, PostgreSQL migration, dependency audit and isolated scanner egress validation required. Any unrun gate is BLOCKED, never PASS.

## 0.2 intelligence and regression gates (defined before implementation)

- Trusted-source sync: fixed HTTPS source adapters only; bounded payloads and pagination, no source-controlled redirects/URLs executed. Invalid feed fails atomically without advancing success cursor. Six/twelve-hour configurable schedule; persistent attempts, retry backoff, and last success. A source record is provenance-verified, never proof of asset exploitability.
- Knowledge: immutable content-hashed revisions with references and explicit review approval. Retrieval uses approved revisions; no source text becomes code, authorization or a scanner rule. Rule activation is limited to code-shipped, fixture-tested detectors with explicit admin approval.
- Inventory matching: customer supplied exact package ecosystem/name/version; no fingerprinting. Explicit supported version match is a confirmed inventory match, NOT confirmed exploitation. Unsupported/missing version semantics remain potential/unverified. Tenant-specific deduplicated alerts; corrections/withdrawals remove stale matches.
- Monitoring: durable due-time and run receipts, atomic claims and queue outbox; no duplicate job per schedule slot. Current authorization, exact scope, asset verification, pause and cooldown remain mandatory. Expired authorization blocks and notifies, never renews silently.
- Remediation: applied-change evidence, customer approval, rollback/staging requirements; enqueue complete supported safe profile. Immutable baseline plus complete rule manifest; categorize resolved/unresolved/new/unverified. Never resolve unsupported or inapplicable checks. Failed retest blocks closure; original still present reopens.
- Test each new API and background flow with deterministic fictional advisories and owned fixtures. Live provider connectivity and full deployment are separately reported; no mock results presented as live intelligence.
