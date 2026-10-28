# Online deployment preparation — 2026-10-25

User direction: deliver for online upload, not a new local Docker installation.
Primary instructions: DEPLOY.md. No cloud resources were created or billed.

Executed evidence:
- Backend regression: **104 passed, 1 skipped**, 50.27s, one upstream deprecation
  warning. JUnit: backend-online.xml; coverage-online.json: **88.63534675615213%**.
- The skipped check requires isolated Redis. Separately executed
  `python scripts/test-with-redis.py` against a real temporary Redis process:
  **2 passed**, 5.50s (redis-journey.log). Actual fixture + Celery broker journey and
  Redis rate limiting passed. This is not a PostgreSQL or cloud acceptance result.
- Full frontend verification before deployment guard test discovery: **18 passed**,
  TypeScript and Next build passed (frontend-online.log).
- Targeted final deployment guard and connections UI tests: **4 passed**, 0.972s.
  Deployment tests were renamed to .tsx to match the configured test discovery.
- Ruff and `bash -n scripts/build-server.sh` passed.
- systemd unit verification reported missing `/srv/aegis/.venv/bin/python` in this
  build environment. Unit execution is **unverified**, not marked passing.

Implemented: PostgreSQL connection components preserve special password characters;
connection pool validation/timeouts; schema-current and Redis readiness; admin-only
live diagnostics; Firebase credential project check and Auth probe; TLS/authenticated
SMTP; public deployment configuration guard; native systemd service definitions,
Caddy configs, build entrypoint and Vercel HTTPS backend validation.

Unexecuted: native production installation, live PostgreSQL, actual Firebase account
connection, actual SMTP inbox delivery, Vercel deployment, browser/mobile acceptance,
cloud backup/restore and independent security review. Hosting for API/workers/database
has not been supplied; existing Firebase and Vercel accounts do not provision this
architecture's backend. No complete-product or production-ready claim.

Full-spec gaps still include invitations, MFA/step-up, provider ownership connectors,
reviewed code patches, safe attachments/support, broader scan profiles and external AI.
Existing deterministic guidance, authorization and no-payment controls are retained.

## Supplied Firebase public configuration

The online environment template now contains the user-supplied public apiKey. All public
SDK values are preserved in packages/configuration/firebase.public.json. Auth-only use
is unchanged. Focused config/identity regression: 8 passed in 1.63s; see
firebase-public-config.log. This verifies configuration propagation and existing mocked
identity contracts, not actual Google sign-in or a live Firebase server connection.
