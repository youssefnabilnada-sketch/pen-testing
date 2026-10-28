# Current engineering checkpoint — Cloudflare response and authorization safety

**Development source only. NOT certified for public production.** Continue from the previously saved `2a9875b` Cloudflare SmartVerify checkpoint; no older source restored and no external websites scanned or DNS modified.

## Changes in this checkpoint

- `apps/api/aegis/cloudflare_verify.py`: receive fixed Cloudflare API replies as bounded 4-KiB chunks, refuse oversized declared or actual response bodies while streaming, fail closed on bad HTTP/JSON, and never follow redirects or environment proxies. The response limit is 65,536 bytes. The limit controls application buffering; it does not certify every upstream network/memory resource bound.
- Normalize registered site and Cloudflare zone hostnames using IDNA for accurate exact/subdomain label-boundary checks, without accepting cross-zone DNS writes.
- Fail closed on non-text DNS record fields and invalid record-list pagination metadata rather than crashing or reporting an unverified result as successful.
- Recheck current permission and challenge even when an existing matching TXT proof is returned. This avoids reporting an idempotent success after known authorization revocation.
- Extended isolated provider contract coverage: Cloudflare redirect rejection, response size limits, malformed data, internationalized hostnames, and revocation on duplicate proofs.

## Tests executed in this container

- `PYTHONPATH=apps/api python -m unittest discover -s tests -p 'test_*unit.py' -q`: **36 passed**.
- `test_discovery_deadline.py`: **4 passed**.
- `test_crawler_html_resilience.py`: **4 passed**.
- `test_discovery_grants.py`: **3 passed**.
- Total above: **47 isolated Python tests passed** (distinct selections; these do not replace the integrated suite).
- `php -l integrations/wordpress/aegis-verify/aegis-verify.php`: **passed**.
- `php tests/wordpress_contract.php`: **passed**, contract double only; not a real WordPress bootstrap.
- `python -m compileall -q apps/api/aegis/cloudflare_verify.py tests/test_cloudflare_provider_unit.py`: **passed**.
- `git diff --check`: **passed**.
- API integrated pytest attempted: **blocked before collection** by absent `celery`, not an application assertion result. `pip` did not provide the missing package in this environment. The `apps/web/node_modules` tree, real PostgreSQL, Redis, and full WordPress runtime are not provisioned here.

## What is still required before any public launch

1. Fully provision dependencies; run all `pytest tests --cov=aegis --cov-fail-under=85`, full Next/Vitest/Playwright and focused Cloudflare integration; fix genuine failures. Last recorded prior full backend run was *not* all-green on a frozen source tree.
2. PostgreSQL schema migration `014–017` on an isolated server plus backup/restore; Redis background workers/beat durability, SMTP, Firebase live authorized login, and website-monitor dispatch acceptance.
3. Actual disposable WordPress plugin installation and owner-controlled Cloudflare DNS propagation test with a disposable least-privilege token. Complete necessary SmartVerify provider choices or explicitly remove unfinished promised features from launch scope.
4. AutoFix staging, explicit approval and rollback, whole customer Scan→preview→fix→retest journey; Launch Guard/API/Agency/CRM/Vault/admin/report and tenant isolation browser acceptance.
5. User-owned private GitHub CI, online service accounts, correct secrets and hostnames, security review, alerting, restore-tested backups, incident/privacy/support processes, and live cloud acceptance before publication.

Preserve current decisions: pricing/payments/checkout and conversational AI disabled, ownership proof separate from scan authorization, scan separate from approved AutoFix, no automatic public deployments or unauthorized target tests. Do **not** call this ZIP a release candidate until the independent gates pass.
