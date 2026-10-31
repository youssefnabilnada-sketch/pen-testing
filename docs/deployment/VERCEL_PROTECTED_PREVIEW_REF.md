# AEGIS protected Preview branch registration

This branch is reserved for a single isolated Vercel Preview gateway acceptance run.

- Base integration SHA: `9e5f1e70d88a6bc30de4e15afd2cc9e557a95b48`.
- This documentation-only branch commit intentionally distinguishes the protected Preview Git ref from its base commit for Vercel branch-scoped environment validation.
- It must not be merged solely to change a Vercel configuration; preserve the active Oracle/backend deployment and production alias.
- Enable protected Preview auth only once the Caddy gateway and matching server-only secret exist. Without them, fail closed.
- Production registration, scans, scheduler, paid services and customer access remain disabled.
- Verify real browser session, email delivery, CSRF, logout, tenant isolation, and ability to revoke access after testing.
