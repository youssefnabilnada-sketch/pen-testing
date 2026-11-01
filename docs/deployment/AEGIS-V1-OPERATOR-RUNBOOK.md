# AEGIS v1 — final release operator runbook (single existing Vercel + Oracle)

**Current status: release candidate. NOT public-launch approved.** This is for the existing `pen-testing` project, public hostname `aegis-pentest-eg.vercel.app`, and the existing Oracle ARM server. Do not create another project or preview deployment. Never paste private keys, tokens or a gateway secret into chat, GitHub or terminal command arguments.

## 1. What engineering completed and verified
- Release branch: `release/aegis-v1-final` / draft PR #15.
- Combined Astra features, isolated PostgreSQL/Redis/WordPress/browser tests, restricted production Next.js proxy, account throttling, registration closed by default, Caddy production-only gateway template and guarded Oracle release/rollback tooling.
- Vercel project environment: `API_INTERNAL_URL` is already correct for both Preview and Production (`https://aegis-pentest-eg-api.duckdns.org`).
- Vercel **Production-only** `AEGIS_PRODUCTION_GATEWAY_ENABLED=false` was safely created. Do not enable yet.
- `AEGIS_PRODUCTION_GATEWAY_KEY` is now created as a Vercel Production-only **Secret**, and the Oracle Caddy Production gateway was installed successfully by the operator. A previous screenshot exposed part of the first key; **rotate it before enabling traffic**. Never re-run the first-time `oci-production-gateway.sh --install` on an installed gateway.
- CI must finish successfully on the exact **latest** release SHA; do not rely on a passing historical SHA.

## 2. One-time operator preparation on Windows
Generate and save a 64-character random URL-safe key using a trusted password manager, or run in PowerShell (the key goes to the clipboard, never appears in the terminal):

**Use the following single PowerShell line, all at once** (avoids partial execution / null variables in Windows PowerShell 5.1). It checks the generated key length before copying and never prints the key:

```powershell
& { $bytes = New-Object byte[] 48; $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create(); try { $rng.GetBytes($bytes); $secret = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_'); if ($secret.Length -ne 64) { throw 'Gateway key generation failed' }; Set-Clipboard -Value $secret; Write-Host 'SUCCESS: 64-character gateway key copied to clipboard' } finally { $rng.Dispose() } }
```

If any red PowerShell error appears, **STOP**: discard clipboard contents and do not paste anything into Vercel. The earlier multi-line variant could report a misleading success after null-variable errors.

Keep the key in a secure password manager so the same value can be pasted **privately** into both destinations. Clear the clipboard when finished.

SSH to the existing VM in Windows PowerShell (the private key is only used locally):

```powershell
ssh -i "$env:USERPROFILE\Downloads\ssh-key-2026-10-30.key" ubuntu@158.101.189.39
```

## 3. Isolated final checkout on Oracle — no live changes
Run in Ubuntu SSH (not Windows PowerShell). This creates a detached worktree and leaves the original checkout / running services intact:

```bash
cd /home/ubuntu/aegis-cloud
# This OCI checkout has a single-branch fetch refspec. An unqualified
# 'git fetch origin' updates only deploy/oracle-always-free-prep-20261028.
# Explicitly fetch exactly the existing release branch, without touching
# the local deployment branch or changing Git's persistent configuration.
git fetch origin refs/heads/release/aegis-v1-final:refs/remotes/origin/release/aegis-v1-final
git show-ref --verify refs/remotes/origin/release/aegis-v1-final
git worktree add --detach /home/ubuntu/aegis-v1-final refs/remotes/origin/release/aegis-v1-final
cd /home/ubuntu/aegis-v1-final
bash scripts/oci-v1-backend-rollout.sh --check
bash scripts/oci-production-gateway.sh --check
```

If you previously saw `fatal: invalid reference: origin/release/aegis-v1-final`, it was because the OCI Git remote is configured to fetch only the legacy deploy branch. The exact-ref fetch above fixes that without changing any tracked source, running service or production deployment. Do not run `--apply` or `--install` when a previous `cd` or worktree command has failed.

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
- Keep `AEGIS_PRODUCTION_GATEWAY_ENABLED=false` until the **newly rotated** gateway key is installed in both Oracle and Vercel and the operator reports `AEGIS_PRODUCTION_GATEWAY_ROTATED_PASS`. Do not set true on your own.
- Existing Production `API_INTERNAL_URL` has already been checked and needs no change. Avoid branch-scoped Preview env; Vercel API is rejecting that mode (GitHub issue #13).
- Confirm Firebase Authentication Authorized Domains includes `aegis-pentest-eg.vercel.app` and the intended providers are enabled. Do not paste Firebase service-account JSON in any chat.

## 5a. Current next action: rotate the already-installed production key (one-time)

This is **not** the original gateway install path. The original v1 backend rollout and Caddy installation have already succeeded, the release is READY on Vercel Production and the Production opt-in flag is **false**. Do **not** repeat their installers. A previous user-submitted screenshot revealed part of the old key.

1. Make a **fresh** 64-character random key locally on Windows using the one-line PowerShell command above; store it in a password manager. It must differ from the existing Oracle/Vercel key.
2. Open the existing Oracle SSH session. Fetch the release branch explicitly because OCI is configured for single-branch fetch. Update **only the detached deployment-helper worktree**, never the running `/srv/aegis-release-v1` snapshot:

```bash
git -C /home/ubuntu/aegis-cloud fetch origin refs/heads/release/aegis-v1-final:refs/remotes/origin/release/aegis-v1-final &&
git -C /home/ubuntu/aegis-v1-final -c advice.detachedHead=false switch --detach refs/remotes/origin/release/aegis-v1-final &&
cd /home/ubuntu/aegis-v1-final &&
bash scripts/oci-rotate-production-gateway.sh
```

3. At the **hidden** SSH prompt, paste the **new** key, then Enter. Script checks the existing Caddy policy, stages a root-only env file, validates the policy, atomically replaces Caddy's key, checks wrong/public key denial, and restores the old value on failure. Expected: `AEGIS_PRODUCTION_GATEWAY_ROTATED_PASS`.
4. In the existing Vercel project Environment Variables UI, edit `AEGIS_PRODUCTION_GATEWAY_KEY` (Type Secret, Production only) and replace it with this **same new key**. Save and never send a screenshot showing any portion of it. Keep `AEGIS_PRODUCTION_GATEWAY_ENABLED=false`.
5. Only after steps 3 and 4 succeed may the engineer enable the flag and redeploy **the already-approved existing Production release**. Explicitly verify that the deployed source and public domain remain correct. As an additional safe check, from Oracle run `bash scripts/oci-live-web-smoke.sh`; expected `AEGIS_PRODUCTION_SAFE_GATEWAY_SMOKE_PASS`. This uses invalid JSON only and no user credentials.
6. Then perform a **real, authorized** customer browser sign-in, Firebase identity and Brevo email check, session/CSRF/logout/tenant permissions, and authorized asset/scan/report/FastFix acceptance. Existing production registration stays **off** until approval. These cannot be marked passing solely from the safe no-credentials script.

If the rotation script returns `STOP` or `ROLLBACK`, do **not** enable the Vercel flag. The safest stop is Vercel `AEGIS_PRODUCTION_GATEWAY_ENABLED=false`.

### Firebase Google sign-in domain and one approved pilot account

- A live screenshot of `/console` showed `auth/unauthorized-domain` in the Firebase Google sign-in flow. Firebase web configuration and server-admin access can be fully healthy while the browser's **current hostname** is not authorized for OAuth. In the SAME Firebase project configured as AEGIS `FIREBASE_PROJECT_ID`, use **Firebase Console → Authentication → Settings → Authorized domains → Add domain** and add **`aegis-pentest-eg.vercel.app`** (without `https://` or slash). Do not whitelist arbitrary Vercel previews or open Firebase API key restrictions. Retest Google popup on the exact production hostname after saving. If already present, inspect browser API-key restrictions and project matching rather than adding unrelated domains.
- Production registrations are intentionally rejected even though the gateway is live. Never set `AEGIS_PUBLIC_REGISTRATION_ENABLED=true` merely to create an operator test account.
- A **single safe operator-owned pilot**, with email verification, can be provisioned via `scripts/oci-provision-pilot-account.py`. This helper (1) accepts only an owned Gmail `+aegis-pilot` alias, (2) requires an explicit authorization phrase and secret password typed only in SSH, (3) verifies protected production config still has public signup disabled, (4) drops root privileges to the API service user, (5) creates exactly one ordinary unverified user on existing PostgreSQL and sends one AEGIS Brevo email, and (6) assigns no tenant, superadmin or scan authorization. The operator must confirm the emitted `AEGIS_ONE_PILOT_ACCOUNT_CREATED` signal and verify email through the real AEGIS browser; a green CI syntax check **is not** a live account acceptance result.

```bash
git -C /home/ubuntu/aegis-cloud fetch origin refs/heads/release/aegis-v1-final:refs/remotes/origin/release/aegis-v1-final &&
git -C /home/ubuntu/aegis-v1-final switch --detach refs/remotes/origin/release/aegis-v1-final &&
cd /home/ubuntu/aegis-v1-final &&
sudo /srv/aegis/.venv/bin/python scripts/oci-provision-pilot-account.py
```

- Use `yourname+aegis-pilot@gmail.com` (same owned mailbox). The script asks for a **new** strong password twice and `CREATE ONE PILOT ACCOUNT` to authorize the one real account. Do not post password, verification token, browser session cookie, or server environment in chat/issues.
- This pilot account is a real database account, **not automatically cleaned up**. For final signoff verify its inactive/retained-audit status and remove any temporary workspace/assets if created. Do not use it to scan a website before verifying ownership, approved scope, SSRF guardrails and rate limits. Do not test FastFix against production AEGIS itself.
- Existing production source app currently does not have a privileged test-signup bypass; future reviews must not add one to public HTTP APIs.

### Production gateway already enabled — guard against stale acceptance instructions

The Vercel Production gateway was enabled and deployed only after the private-key rotation. Therefore do **not** run `scripts/oci-protected-email-acceptance.sh`: that legacy isolation wrapper explicitly requires the public Vercel auth routes to return HTTP 503 and cannot pass once the protected gateway is in service. Do not toggle public signup or turn off the operational production gateway to force that test to pass. The read-only Oracle checks and separate one-email SMTP probe are safe; they establish connection and mail delivery only. A real user-account browser test needs an approved existing test identity or a separately reviewed test-only provisioning procedure, and proof of cleanup. Avoid testing password reset with an unrelated customer account.

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
