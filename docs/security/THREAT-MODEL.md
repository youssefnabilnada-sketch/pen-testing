# Threat model — local checkpoint

| Boundary / threat | Implemented protection | Residual risk / required gate |
|---|---|---|
| Tenant ID substitution | Stored-resource org membership checks; roles enforced server-side; adversarial API tests | Add PostgreSQL RLS/DB roles and a full tenant-route matrix before pilot |
| Session theft / forged write | Argon2 password hashes; random hashed session token; HttpOnly SameSite Strict cookie; CSRF token and origin check; logout/reset revoke sessions | Local HTTP uses Secure=false explicitly; TLS proxy, cookie Secure=true, account lockout controls and MFA needed for public environments |
| Network pivot / DNS rebinding | Canonical origin parser; block nonglobal/mapped/transition IPs; validate all DNS answers; connect pinned IP; TLS SNI and hostname verification; proxies ignored; redirects rejected | OS DNS resolution timeout, firewall/DNS equivalence and adversarial proxy cases still need independent review |
| Local fixture escape | Exact host and exact single private IP exception behind server environment switch; isolated Compose networks | Docker network isolation must be validated on an actual host; never enable this exception in production |
| Scanning without current consent | Expiring ownership and scope records; launch/worker checks; cancellation on revoke/pause | TOCTOU at network boundaries cannot recall a request already sent; bounded request finishes or times out |
| Abuse / overload | One GET; socket timeout; 10-second socket watchdog; Celery hard limit; Redis per-origin 60s cooldown; one worker; auth and verification throttle | Public quota policy, fair queueing and comprehensive per-user mutation rate limits deferred |
| Worker compromise | Non-root worker, read-only filesystem, dropped capabilities, memory/CPU limits, no AI/API keys | Worker currently shares database credentials and control network; split scanner from DB/broker access before pilot |
| Prompt injection | No remote LLM active; deterministic explanations accept only known rule IDs; raw body is not forwarded | External provider integration, structured output validation and timeout/injection tests deferred |
| Secret leakage | Body not persisted; cookie values/names omitted; predefined evidence; no raw HTML report rendering | General secret scrubber, retention/deletion policy enforcement and incident processes deferred |
| Report access | Membership check on immutable report record | Signed object-storage URLs/attachment scanning not implemented; no file upload endpoint exists |
| Workflow forgery | Scoped roles, quote state checks and locked acceptance/task transitions; no direct resolved state action | Versioned quotes and stronger concurrency constraints for duplicate remediation requests deferred |
| Incomplete job mistaken for secure | Only successful checks persist/resolve results; explicit failed/cancelled state; no security-score claims | Full partial-result semantics are not implemented; HTTP non-2xx and certificate errors are failures |

## Release decision

**Not production-ready; not yet cleared for an external authorized pilot.** Local development and controlled testing only. Browser security policy blocked visual QA. Docker/PostgreSQL/Redis stack and egress controls were not executed here. Resolve these blockers and the documented missing scope before any public exposure. No public network assessment was performed during development.

## 0.2 intelligence boundary

Advisory ingestion is separate from assessment execution and runs in a dedicated egress-enabled container. Only fixed official endpoints are fetched; redirects and arbitrary reference crawling are denied. Records are source data, not executable rules. Immutable revisions require approval before deterministic knowledge retrieval; inventory matches remain separate from runtime findings. Source text is never allowed to authorize scans. Full retest comparisons retain unsupported checks as unverified and block closure. Outbox retries apply to scheduled and remediation jobs. Real network containment, PostgreSQL concurrency, source availability, multi-process scheduler recovery and catalog-scale performance remain unverified release gates. The intelligence worker still shares database credentials; least-privilege credentials must precede a pilot.
