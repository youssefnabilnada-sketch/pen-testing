# Detector and operations change review

## Implemented boundaries

- Optional detectors are code-owned catalog entries, inactive until matching-version
  fixture validation plus administrator approval. A failed revalidation revokes activation.
  The execution gate independently validates persisted version and fixture evidence.
- First CSP directive occurrence wins in the limited parser. Multiple-policy semantics
  are not approximated as fixed; affected checks are explicitly unverified.
- Absent/malformed cookie evidence cannot verify previous cookie observations fixed.
  Candidate evidence excludes cookie names and values.
- Global operations records require superadministrator access before querying. Explicit
  field lists exclude hashes, tokens, MFA secrets and raw observations. Page sizes are bounded.
- Recovery sets cancellation and failed state, records audit/notification, marks retest
  unverified and updates scheduled status. Workers stop at terminal-state checkpoints.
- Finding search/count/history are tenant-scoped; asset joins require the same tenant.
  Sorts are an allowlist. Literal wildcard escaping avoids accidental broad search.
- AI output cannot become code, a vulnerability claim, an authorization or a verified fix.
  Only effort enums for supplied catalog rules are accepted. External advice is optional.

## Unverified and remaining constraints

- SQLite tests do not prove PostgreSQL locking/race behavior. Multi-process recovery,
  cancellation and result commit races still require PostgreSQL concurrency acceptance.
- Browser accessibility/mobile verification is not performed in this environment.
- No live model provider or customer/public target is contacted by these tests.
- DNS resolution is OS-bound and not included in the socket transport deadline.
- The supported assessment remains a single authorized root response. No crawl,
  authenticated application testing, advanced exploitation or full pentest coverage.

## Parser references

https://www.w3.org/TR/CSP3/
https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie

References inform bounded configuration checks. They do not certify application security.
