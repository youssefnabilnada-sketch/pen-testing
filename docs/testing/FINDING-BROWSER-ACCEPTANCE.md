# Finding browser acceptance criteria

- Organization membership enforced before querying; pagination never crosses tenant boundaries.
- Title/asset/rule search, severity/status filtering and stable sort operate server-side over all findings.
- Bound page sizes and filter lengths; reject unknown sort fields and invalid filters.
- Join assets once per page; return a count using the same predicates.
- History requires the finding's tenant membership, includes real observed/review events and supports pagination.
- A customer can browse older findings instead of silently searching only the first 100.
- UI provides explicit loading/error/empty distinctions, next/previous, review and remediation actions; viewers cannot mutate.
- Backend tests cover multiple pages, sorting/filtering, tenant isolation, history and invalid input. Component tests cover navigation and failure.
