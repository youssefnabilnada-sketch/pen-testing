# Reviewed detector expansion acceptance
Extend the code-owned registry with CSP base-uri presence and explicit SameSite cookie
configuration checks. New rules are disabled until a platform administrator validates
fixed positive, negative and inapplicable fixtures and explicitly approves that version.
Never execute feed-provided code or activate a newer detector using older evidence.
Allow disabling without losing history. Retests include every active applicable rule;
missing cookies or unsupported/multiple CSP policies produce unverified, never fixed.
Correct CSP parsing to preserve the first repeated directive and avoid mistaking a
directive-name substring in a reporting URL for an actual directive. Evidence omits
cookie values and header contents. Findings describe configuration observations, not
proven exploitation. Tests cover review gates, stale version, unknown rule rejection,
disable, redaction, applicability and resolved/new/unverified comparisons.
