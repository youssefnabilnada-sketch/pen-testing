# Production / authorized pilot release gate

This checklist is not an approval to deploy.

- [ ] Execute full Compose acceptance and retain worker, API, DB, email and browser evidence.
- [ ] Verify PostgreSQL migrations, transaction contention, duplicate job races and tenant constraints.
- [ ] Separate scanner network process from DB, Redis and application secrets; enforce destination allowlists at the egress layer.
- [ ] Disable and remove local fixture mode/profile in production.
- [ ] Independent review of SSRF, DNS rebinding, IPv6, IDNA, redirect and slow-response defenses.
- [ ] TLS reverse proxy, HTTPS-only cookies, restrictive production CSP, host validation and correct trusted-proxy configuration.
- [ ] MFA for privileged users; recovery, invitation acceptance, role-removal and account lifecycle completeness.
- [ ] Strong random secrets from a secret manager; least-privilege database credentials and audited admin bootstrapping.
- [ ] Transactional outbox / reconciliation for DB-versus-queue delivery failures; durable job lease/heartbeat and supervised recovery.
- [ ] Rate-limit all abuse-sensitive endpoints; fair queueing, per-org storage quotas and resource limit tests.
- [ ] Resolve all applicable high/critical dependency audit findings, including dev/build supply chain.
- [ ] Desktop/tablet/mobile visual review; keyboard, contrast, screen reader, reduced motion and WebGL fallback checks.
- [ ] Implement retention and deletion jobs; test backup restoration, report removal and audit retention policies.
- [ ] Define incident response, customer authorization agreement, privacy notice and support ownership with appropriate review.
- [ ] Measure p95 API latency, queue lag, browser loading, DB queries and scan resource usage under representative load.
- [ ] Complete requirements-gap checklist in HANDOVER before describing the full requested product as delivered.
- [ ] Payments remain disabled until the user separately authorizes their implementation.

## Backup / restore procedure (must be exercised on a disposable restore target)

PowerShell-safe binary dump handling:

```powershell
docker compose exec db pg_dump -U aegis -Fc -f /tmp/aegis.dump aegis
docker compose cp db:/tmp/aegis.dump ./aegis.dump
```

Encrypt/restrict the backup; it contains customer data and password hashes. Restore only into an approved isolated environment, never overwrite a live DB casually. Copy the dump into that environment, run pg_restore into a newly created database and check migrations, tenant counts and report access. Backups are not proven until a restore is tested. Current automated retention/deletion and restore verification are deferred.
