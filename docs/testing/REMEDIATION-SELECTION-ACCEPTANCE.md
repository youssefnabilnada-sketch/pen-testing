# Remediation selection acceptance

- Existing one-click requests remain compatible and default to all eligible findings.
- A customer can select critical, critical-and-high, or all eligible findings for an asset.
- Server authorizes organization/role, validates selection and excludes resolved, accepted-risk and false-positive findings.
- Existing active tickets are reused. Individual and bulk creation acquire the same asset lock before checking active tickets.
- Empty selections return zero, explicitly explaining that no request/fix was made.
- Response reports created/reused counts and preliminary estimate disclaimer, never payment or repair success.
- UI uses explicit review language and exposes the selection to keyboard users; no ownership or deployment authorization is implied.
- Tests cover severity selection, exclusions, duplicate requests, tenant/viewer denial, invalid selection and user interaction.

## Remediation browser
- Searchable-by-status pages return matching total and deterministic order; maximum 100 per page.
- Tenant/role checks precede page queries. Asset ID/title come from matching tenant findings.
- Customer UI provides previous/next controls and resets offset on organization/filter change.
- Existing list API remains backward compatible; regression tests seed more than 100 rows.
