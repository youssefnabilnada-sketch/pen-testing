# Repository integration acceptance

Acceptance: explicit owner/admin connection; OAuth state single-use, expiring and bound to user/workspace; encrypted credentials and proposal bytes; scoped repository selection; fixed provider endpoints; draft PR only after exact-diff approval and MFA; base SHA changes reject publication; failure never implies success; PR merge never resolves a finding or triggers unauthorized assessment.

Supported generator: existing vercel.json, missing X-Content-Type-Options, reviewed nosniff addition. JSON and preservation checks run without executing repository code. Application CI is retrieved after PR publication; staging and full security retesting remain explicit existing remediation actions. No automatic merge, no production deployment, no arbitrary remote shell/test scripts.

Limits: GitHub operations tested with deterministic provider fixtures, not a live installation. Only the default branch is supported. Initial repository UI lists one page (API supports pagination). Expired credentials require reconnect. Ambiguous publication requires manual inspection; it is not blindly retried. No general-purpose AI patch generation or isolated arbitrary-code CI runner is claimed.

Runtime investigation: apt-get update returned exit 100 with `setgroups (1: Operation not permitted)` and `seteuid (22: Invalid argument)`. PostgreSQL/Docker are absent. This blocks that local infrastructure installation path, not ordinary code execution. No usage/context/tool exhaustion error was observed.
