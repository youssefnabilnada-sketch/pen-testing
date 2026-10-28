# AEGIS 0.3 development checkpoint

This is an incremental checkpoint, NOT the completed requested cloud/connector release.
Read docs/deployment/FIREBASE-AND-GITHUB.md before enabling Firebase.

## What changed
- Ownership guide recovers current challenges after reload, preserves unexpired tokens,
  offers copy and GitHub prefilled-file assistance for static root or public/ projects.
- Revoking ownership invalidates outstanding challenges.
- Visible consent checkbox and explanation when assessment launch is disabled.
- One-click engineer review for all eligible findings of an asset, reusing open requests.
  Nothing is automatically modified or marked fixed.
- Optional API-only Firebase identity linking/login/unlink, explicit linking with password
  reauthentication; no email auto-link or domain ownership inference.
- Optional App Hosting template; not deployed and not a promise of free cloud hosting.
- Local-access Compose overlay includes the Windows networking adjustment.

## Safe Windows upgrade
Keep the old folder and your .env. Back up PostgreSQL before migrations. Never use
`docker compose down -v`: it destroys the database volume. Do not upload .env to GitHub.
Extract the new archive to another folder, copy your existing .env into its project
folder, then open PowerShell there. The Compose project name is unchanged, so it
addresses the existing local volumes. Back up before proceeding.

Backup (creates a dump inside the DB container, then copies it to your current folder):
`docker compose exec db pg_dump -U aegis -d aegis -Fc -f /tmp/aegis-backup.dump`
`docker compose cp db:/tmp/aegis-backup.dump ./aegis-backup.dump`
Keep this backup private and outside any GitHub upload.

Run each line separately:
`docker compose -f docker-compose.yml -f docker-compose.local-access.yml build`
`docker compose -f docker-compose.yml -f docker-compose.local-access.yml run --rm migrate`
`docker compose -f docker-compose.yml -f docker-compose.local-access.yml up -d`
Open http://localhost:3000/console. Existing credentials/data should be retained;
PostgreSQL upgrade has NOT been executed in our environment, so verify your backup.
SQLite migration roundtrip is covered by the automated suite.

## Tests
`pip install -r apps/api/requirements-dev.txt`
Linux: `PYTHONPATH=apps/api pytest tests -q --cov=aegis`
PowerShell: `$env:PYTHONPATH='apps/api'; python -m pytest tests -q --cov=aegis`
`npm --prefix apps/web ci`
`npm --prefix apps/web run typecheck`
`npm --prefix apps/web test`
`npm --prefix apps/web run build`

## Not finished / release blockers
- Firebase browser sign-in/link UI and live cloud integration validation.
- GitHub App/OAuth and direct hosting/DNS provider integrations.
- Automated tested patches, staging deployments, MFA step-up and approved production
  deployment. Existing engineer-managed service remains available instead.
- Full Docker/PostgreSQL/Redis integration and desktop/mobile browser validation here.
- Optional Firebase dependency lock/audit. No promise all old behavior is unchanged
  beyond regression evidence. Original checkpoint limitations still apply.
Payments remain disabled. No provider installed or payment required for remediation.
