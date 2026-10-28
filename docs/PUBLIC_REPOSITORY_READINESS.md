# Public repository readiness — security gate

**Status: NO-GO for public release until independently approved.**

The current GitHub CI baseline and the Universal FastFix branch do **not** establish that this private repository can safely become public.

## What this additional gate does

- Uses a full-history checkout to examine reachable Git object content and historical file names, including previously deleted files.
- Looks for a narrow set of high-confidence credential/private-key indicators without printing secret values.
- Blocks on suspicious sensitive filenames or files too large to inspect.
- Includes local isolated tests proving that a deleted .env remains detectable.

Run on a full-history checkout: `python scripts/check_public_repo_history.py`.

## What this gate does NOT prove

It cannot exhaustively detect all secrets, private user or customer data, copyrighted third-party materials, or private information hidden in large/unreachable objects, GitHub releases, issues, attachments, Actions artifacts, external hosting, or container layers. It also does not establish legal rights, project license, security of the deployed SaaS or operational safety.

Before changing visibility:
1. Audit ALL code, history and external artifacts for secrets and personal data. Revoke/rotate any exposed credentials **before** rewriting history, if necessary.
2. Decide and document a license (none is present in the repository root at this checkpoint), IP ownership and third-party redistribution rights.
3. Inspect public-facing configuration, domain information, Firebase web configuration and project metadata.
4. Ensure committed examples contain placeholders only. Never store production service-account credentials or environment secrets.
5. Run the entire current CI and an independent public-release review on the precise candidate commit.
6. Obtain verified real staging evidence for authentication, scanning, AI, FastFix, notifications, recovery and infrastructure before claiming production readiness.
7. Make visibility changes separately through GitHub owner Settings only after explicit final owner review; making a repo public exposes prior commits, not just the newest source.

Keep billing and public AI disabled pending authorization and evaluation. GitHub publication and customer SaaS deployment are separate decisions.
