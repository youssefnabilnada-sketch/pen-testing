# API contracts

The generated `openapi.json` is the authoritative route/schema contract for this checkpoint. Interactive documentation is at `http://localhost:8000/docs` when running locally.

Authentication: session cookie `aegis_session`. Retrieve current user/CSRF through `GET /auth/me`; include `X-CSRF-Token` for authenticated mutations. Same-origin browser requests go through the Next `/api` proxy. No bearer-token or external CORS access is enabled.

Public auth routes: POST register, login, verify, reset-request, reset. Authenticated logout and deactivate revoke sessions. Organization and asset routes use stored membership. Platform administrator routes live under `/admin` and require an explicit superadmin flag.

Errors use FastAPI `{ "detail": ... }`. 401 unauthenticated; 403 permission/authorization; 404 absent; 409 state conflict/duplicate; 422 invalid data or scope; 429 rate limit; 503 unavailable coordinating service. Health does not assert complete service health: `/health` verifies database reachability; `/admin/health` probes queue and workers separately.

List limits: findings support q, severity, status and offset, limit 100. Jobs, assets and other list endpoints have limited pagination in this checkpoint. Audit UI shows a bounded recent history. These are not unlimited production-scale APIs.
