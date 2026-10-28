# Database and identity integration acceptance

Before implementation, required outcomes:

1. Connection diagnostics exercise SQL, migration state, Redis PING and worker replies.
   Unavailable services must return degraded status, never invented availability.
2. Firebase settings and server credentials must refer to the same project; server
   identity must be initialized and tested against the Auth API without retrieving
   customer account lists. Missing credentials are a configuration failure, not an
   incorrect-password message. Public configuration never contains credentials.
3. Windows launcher preserves an existing database password, generates one only for
   new installations, uses local-only published ports, applies migrations, waits for
   real readiness, and never deletes volumes. Firebase credential files stay outside
   the repository and are mounted into API only. No payment provider is introduced.
4. PostgreSQL uses bounded connection timeouts and validates stale pooled connections.
   Passwords are supplied as separate connection components, avoiding URL interpolation
   bugs when an operator uses punctuation in a password.
5. Tests exercise failure/redaction/project mismatch, readiness, service permissions,
   actual Redis broker execution when available, and preserve existing journeys.
6. Running a command or saving config is not proof of a live Firebase connection.
   Cloud verification and the full container stack require actual execution evidence.
