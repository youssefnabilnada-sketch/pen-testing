# Integrated API additions

All routes require an authenticated session; mutation routes also require CSRF.
OpenAPI contains exact query constraints and schemas.

- GET `/admin/operations`: persisted counts, source sync timestamps and configuration state.
- GET `/admin/operations/records/{kind}`: bounded organizations/users/assets/jobs.
- GET `/organizations/{org_id}/finding-page`: total/items, literal title/rule/origin search,
  severity/status filter, recent/oldest/severity sorting, offset and limit (max 100).
- GET `/findings/{finding_id}/history`: tenant-checked, paginated observed/review events.
- POST `/admin/intelligence/rules/{key}/validate|approve|disable`: code-owned detector gates.
- GET `/findings/{finding_id}/explanation`: deterministic guidance, independent approved
  retrieved knowledge, optional constrained effort estimates and explicit fallback state.

The remediation list includes its asset ID and finding title so history/retest navigation
is independent of the currently loaded findings page. Legacy list routes remain compatible.
Global service availability remains a separate diagnostic; stored counts do not imply uptime.
