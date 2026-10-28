# Optional model advice boundary

The application works without an AI key or paid service. `AI_PROVIDER_ENABLED=false`
is the default. Deterministic explanations and approved advisory retrieval remain available.

An operator can configure a chat-completions-compatible HTTPS provider using
`AI_CHAT_ENDPOINT`, `AI_MODEL`, and `AI_API_KEY` in the backend's private environment.
The path must end in `chat/completions` and use standard HTTPS port 443. No browser
input or tenant request can change the destination. Credentials must never be committed.
No live provider has been connected or billed by this implementation session.

The adapter implements an `EffortProvider` boundary. It sends only reviewed rule IDs,
rule titles and predefined remediation guidance. It does not send assessed HTML,
headers, secrets, evidence strings, domains, identity or customer files. The output is
limited to a validated rule-to-effort enum mapping. Model output cannot introduce a
finding, change severity, authorize a scan, create a patch or mark a fix verified.
Estimates are preliminary inferences requiring engineer review.

A public-IP-pinned HTTPS connection rejects private DNS answers, redirects and bodies
above 32 KiB. Socket timeout is 5 seconds and post-resolution transport deadline is
10 seconds; OS DNS resolution is outside that deadline. A shared Redis cooldown permits
at most one provider attempt per 30 seconds; unavailable Redis fails to fallback. Tests
skip coordination only under TESTING, which production startup forbids. No automatic
provider retry occurs. Refusal, truncation, invalid JSON, unsupported fields or failures
produce the deterministic response with a generic fallback marker. Provider errors,
credentials and arbitrary returned text are never shown to customers.

This is optional model-assisted effort estimation, not general freeform AI explanation,
AI patch generation, model retraining or validated live-provider connectivity. Official
approved remediation knowledge remains attached independently to the finding explanation.
Reports continue using deterministic summaries for reproducibility.

Protocol reference consulted: https://developers.openai.com/api/docs/guides/structured-outputs
(JSON mode is syntax assistance only; the application validates the complete response.)
