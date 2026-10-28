# Authorized assessment windows
Recurring consent may specify a daily UTC-hour window with start < end, within 0..24.
Default 00:00–24:00 preserves current behavior. Persist the window in immutable consent
scope, display it, and check at enqueue and worker safety checkpoints. The scheduler
defers to the next eligible start before ownership re-verification or job creation.
Outside-window work must not make a request or be interpreted as a clean assessment.
No overnight wrap ambiguity: use one same-day UTC interval. Reject malformed stored
windows. Authorization start/expiry remain enforced. Reserve the transport's ten-second
maximum duration before the closing hour. Tests use controlled clocks and fixture fetches.

Transport rechecks live consent after DNS resolution and again immediately before HTTP
request dispatch. A delayed resolver or connection may not bypass a closing window.
