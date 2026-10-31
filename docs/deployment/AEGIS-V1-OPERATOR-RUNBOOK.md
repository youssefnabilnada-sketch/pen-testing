# AEGIS v1 — final release operator runbook (single existing Vercel + Oracle)

**Current status: release candidate. NOT public-launch approved.** This is for the existing `pen-testing` project, public hostname `aegis-pentest-eg.vercel.app`, and the existing Oracle ARM server. Do not create another project or preview deployment. Never paste private keys, tokens or a gateway secret into chat, GitHub or terminal command arguments.

## 1. What engineering completed and verified
- Release branch: `release/aegis-v1-final` / draft PR #15.
- Combined Astra features, isolated PostgreSQL/Redis/WordPress/browser tests, restricted production Next.js proxy, account throttling, registration closed by default, Caddy production-only gateway template and guarded Oracle release/rollback tooling.
- Vercel project environment: `API_INTERNAL_URL` is already correct for both Preview and Production (`https://aegis-pentest-eg-api.duckdns.org`).
- Vercel **Production-only** `AEGIS_PRODUCTION_GATEWAY_ENABLED=false` was safely created. Do not enable yet.
- `AEGIS_PRODUCTION_GATEWAY_KEY` has NOT been created. The same user-owned strong secret must be entered privately into Vercel and Oracle.
- CI must finish successfully on the exact **latest** release SHA; do not rely on a passing historical SHA.

## 2. One-time operator preparation on Windows
Generate and save a 64-character random URL-safe key using a trusted password manager, or run in PowerShell (the key goes to the clipboard, never appears in the terminal):

```powershell
$b = New-Object byte[] 48
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($b)
$key = [Convert]::ToBase64String($b).TrimEnd('=').Replace('+','-').Replace('/','_')
Set-Clipboard $key
$rng.Dispose()
Remove-Variable key,b,rng
Write-Host "64-character gateway secret copied to clipboard; never send it in chat."
```

Keep the key in a secure password manager so the same value can be pasted **privately** into both destinations. Clear the clipboard when finished.

SSH to the existing VM in Windows PowerShell (the private key is only used locally):

```powershell
ssh -i "$env:USERPROFILE\Downloads\ssh-key-2026-10-30.key" ubuntu@158.101.189.39
```

## 3. Isolated final checkout on Oracle — no live changes
Run in Ubuntu SSH (not Windows PowerShell). This creates a detached worktree and leaves the original checkout / running services intact:

```bash
cd /home/ubuntu/aegis-cloud
git fetch --prune origin
git worktree add --detach /home/ubuntu/aegis-v1-final origin/release/aegis-v1-final
cd /home/ubuntu/aegis-v1-final
bash scripts/oci-v1-backend-rollout.sh --check
bash scripts/oci-production-gateway.sh --check
```

**STOP** unless both report `AEGIS_V1_PRECHECK_PASS` and `AEGIS_PRODUCTION_GATEWAY_PREFLIGHT_PASS`. Do not attempt to hand-edit Caddy on a failed baseline check; report the redacted output for a reviewed patch.

## 4. Guarded Oracle staging — only after both checks pass
Run from `/home/ubuntu/aegis-v1-final`:

```bash
bash scripts/oci-v1-backend-rollout.sh --apply
bash scripts/oci-production-gateway.sh --install
```

The first command stages exact tracked code in `/srv/aegis-release-v1`, refuses changed migrations or dependencies, validates the private API and workers, and retains the previous code release for rollback. It does not touch production databases or Caddy.

The second command requires the SAME strong secret already saved by the operator; paste it at the hidden prompt, never as command-line arguments. It validates Caddy configuration, saves the previous Caddyfile, adds a root-only EnvironmentFile, restarts Caddy, and tests wrong/missing/correct secret behavior using **invalid JSON only** (no customer login or mutation).

Expected final messages:
- `AEGIS_V1_BACKEND_PROTECTED_ROLLOUT_PASS`
- `AEGIS_PRODUCTION_CADDY_GATEWAY_INSTALLED`

If either fails, **STOP** and do not activate Vercel Production. Do not post the secret, environment contents or Caddy adapted JSON. Rollback controls (after reviewing error):
```bash
bash scripts/oci-production-gateway.sh --rollback
bash scripts/oci-v1-backend-rollout.sh --rollback
```

## 5. Existing Vercel project: two server-only Production settings
Navigate to `https://vercel.com/youssefnabilnada-1001s-projects/pen-testing/settings/environment-variables`.

- Add `AEGIS_PRODUCTION_GATEWAY_KEY` as an **encrypted/sensitive server-only** Production variable containing the EXACT user-owned key used on Oracle. No `NEXT_PUBLIC_` prefix, no Preview/Development target. This must never be copied into an issue or support ticket.
- Keep `AEGIS_PRODUCTION_GATEWAY_ENABLED=false` until the Oracle operator has supplied both PASS results and the release source CI passes. Do not set true on your own.
- Existing Production `API_INTERNAL_URL` has already been checked and needs no change. Avoid branch-scoped Preview env; Vercel API is rejecting that mode (GitHub issue #13).
- Confirm Firebase Authentication Authorized Domains includes `aegis-pentest-eg.vercel.app` and the intended providers are enabled. Do not paste Firebase service-account JSON in any chat.

## 6. Controlled Production acceptance (no public registration)
- Engineer uses the **existing** Vercel `pen-testing` project to deploy the reviewed release source as Production only once OCI staging is accepted; never publish an old `main`/ZIP build.
- Production Next.js auth/business APIs remain HTTP 503 while the production opt-in flag is `false`. The FastAPI release also blocks **new local and Firebase customer registration** by default in `AEGIS_ENV=production`, even if Vercel routing becomes enabled. This protects from premature public signups.
- Before opt-in, confirm account test identity, Vercel deployment protection and backend permissions, then explicitly authorize a protected acceptance window. Full live browser flow: verified test user, login, first-party Secure/HttpOnly/SameSite cookie, session/CSRF, logout, roles and cross-tenant denial; Firebase, Brevo real inbox; ownership proof, authorized scope, scan/retest, reports; FastFix staging/PR/rollback.
- Finish accessibility/Arabic checks, independent cloud/network scanner-egress and rate-limit controls, encrypted backup schedule and disposable restore rehearsal, monitoring and incident alerts. Keep payments, AI remote unverified services and recurring scheduler disabled until separately approved.
- Only then approve `AEGIS_PRODUCTION_GATEWAY_ENABLED=true` and `AEGIS_PUBLIC_REGISTRATION_ENABLED=true` and public customer rollout; document the actual tested SHA and post-release checks. Never describe a green isolated CI as end-to-end production acceptance.

## 7. Emergency stop
- First set Vercel Production `AEGIS_PRODUCTION_GATEWAY_ENABLED=false` and redeploy to remove production proxy authorization; verify public Caddy fallback still denies requests without a valid gateway key.
- For Oracle Caddy rollback, use `bash scripts/oci-production-gateway.sh --rollback` (only if Caddy config still equals the script-installed version).
- For code rollback, use `bash scripts/oci-v1-backend-rollout.sh --rollback`. The old `9e5f` release and original systemd override remain in place.
- Never roll back PostgreSQL schema without an independent, reviewed database recovery plan. Do not expose browser tokens or any secret in issue comments/screenshots.
