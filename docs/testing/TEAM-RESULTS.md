# Team and account flow verification — 2026-10-25

Primary target remains online deployment. No GitHub upload, cloud charge or public
assessment was performed. This is not a complete-product release claim.

- Backend: 110 passed, 1 skipped, 1 upstream warning, 82.88s. See team-regression.xml.
- Backend coverage: 89.19608677% measured by pytest-cov (coverage-team.json).
- Frontend: 26 tests, 0 failures, 0 errors; team-frontend.xml.
- TypeScript and Next.js production build passed after the final code edits.
- Ruff and git diff --check passed.
- SQLite migration upgrade/check and upgrade/downgrade roundtrip passed.
- One optional real-Redis test is skipped in the ordinary suite; its separate real
  Redis execution from the online deployment work remains documented in ONLINE-RESULTS.md.

Implemented and exercised: 48-hour workspace invitations, verified-recipient explicit
acceptance, duplicate rejection, email-failure rollback, invitation revocation/expiry,
admin-role boundaries, owner protection, member removal and immediate tenant denial,
inviter authority recheck, invitation history and incoming invitations before workspace
creation. Email verification/reset links prefill the intended form, remove the fragment
from the address bar and never submit an account mutation automatically.

Debugging: the previous migration test expected revision 003; updated the expected head
for 004 and verified the full roundtrip. A new frontend mock initially had an incorrect
TypeScript argument signature; fixed and reran type checking and the production build.

Not verified: live SMTP delivery, PostgreSQL concurrency, desktop/mobile real-browser
acceptance, Firebase cloud authentication and online deployment. MFA, ownership provider
connectors, repository patch/deploy automation, attachments/support and the wider scan
profiles remain incomplete. Payments stay disabled.

Migration 004_team_invitations is required for this source. Existing local installations
need not be replaced while the online release is being completed. Do not delete volumes.
