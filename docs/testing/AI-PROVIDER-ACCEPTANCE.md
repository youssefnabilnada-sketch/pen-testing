# Optional AI provider acceptance

- Default remains deterministic and free of external requests.
- Server operator explicitly enables a compatible chat-completions endpoint, model and credential; no browser/API setting can override its destination.
- HTTPS only, public DNS only, pinned resolved IP, certificate hostname validation, no proxies or redirects, bounded response and deadline.
- The model receives only known rule definitions, not customer domains, evidence, website bodies, cookie values or credentials.
- Output can only assign an enumerated preliminary effort class to the exact supplied known rules. No generated vulnerability claims, code, severity changes, authorization, patches or execution.
- Missing configuration, unavailable provider, timeout, invalid JSON, missing/extra rule, unsupported claim, refusal or truncation causes deterministic fallback with a generic reason.
- Approved source guidance stays attached independently; model output cannot replace official patches or source provenance.
- Tests cover parser, transport contracts, destination validation, failure fallback and tenant-authorized explanation integration. Live paid-provider acceptance is not performed.
