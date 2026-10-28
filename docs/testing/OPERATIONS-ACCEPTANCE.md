# Operations acceptance criteria

- Only a platform administrator can read global operational data; anonymous and tenant members are denied.
- Counts derive from database rows and include every recorded job state, not just a selected subset.
- Paginated organizations, users, assets and jobs return bounded explicit fields only. Password hashes, sessions, MFA and ownership tokens never appear.
- Errors and outbox retry metadata are visible without returning scanned content or secrets.
- Stale-job recovery cancels further execution, marks associated retest unverified, updates monitoring state and creates an audit/notification. It never reports a verified fix.
- A worker observing an already terminal job cannot overwrite recovery or resume network execution.
- UI distinguishes load failure from zero counts and supports pagination and explicit refresh.
- Automated tests: unauthorized access, page bounds, aggregate counts, field redaction, stale retest recovery, worker terminal guard, UI failure/refresh/navigation.
- PostgreSQL concurrent transactions and browser rendering remain separate acceptance gates.
