# Internal integration evidence — 2026-10-26

This records implementation progress, not final product acceptance or a production release.

| Module | Implemented behavior | Executed checks | Result | Outstanding limits |
|---|---|---|---|---|
| Attachments | Text evidence in support/remediation; private-file rules; download/delete; quotas | UTF-8 roundtrip, size/type/control rejection, envelope cap, parent binding, tenant/viewer/staff permissions | Pass | Text only; no malware service, binary files or PostgreSQL concurrency acceptance |
| Notifications | Personal in-app category preferences and per-user read receipts | Default/filter persistence, idempotent read, peer independence, tenant denial | Pass | No email/push preferences or delivery |
| Account | Display name, password change, sign-out-all, guarded deactivation | Current password/MFA, session/token revocation, legacy-route refusal, owner/admin guards | Pass | No email change, erasure or self-service reactivation |
| Ownership | Explicit transfer to active verified existing administrator | Consent, email confirmation, password, role guards, single-owner state, former-owner deactivation | Pass | PostgreSQL race acceptance and real browser flow remain outstanding |
| Database | Migrations through 009_profile | Upgrade, repeat upgrade, schema parity, downgrade, re-upgrade on SQLite | Pass | PostgreSQL migration execution remains unverified |

Final backend suite: **126 passed, 1 skipped**, no failures/errors, JUnit elapsed
**74.359 seconds** (`lifecycle-final-backend.xml`). Measured line coverage:
**91.70506912442396%**, in `lifecycle-final-coverage.json`.

Separate real Redis fixture runner: **2 passed**, 2.97 seconds, `lifecycle-redis.log`.
This covers the queue test skipped by the default suite using isolated local fixtures.
It does not validate a production deployment or customer websites.

Final frontend component suite: **39 passed**, no failures/errors,
`lifecycle-frontend.xml` and `lifecycle-frontend.log`. TypeScript, Ruff and whitespace
checks passed. The initial final-build attempt was interrupted in the runtime, and retries encountered
a runtime library failure and stale export-directory errors. After retaining the old
output outside the project and bounding build workers to two, a complete production
build passed (`windows-build.log`), including the subsequently added window UI.

Corrections during work: misplaced test assertion fixed; native required-file form
validation conflicted with simulated file selection, replaced with the existing explicit
file validation and disabled submit; JSX brace error in preferences fixed. All affected
tests rerun. Legacy unconfirmed account deactivation was found and disabled; its updated
test and the new secure flow pass. Attachment metadata listing avoids reading file bodies.

Commands:
```sh
PYTHONPATH=apps/api python -m pytest tests -q --cov=aegis
python scripts/test-with-redis.py
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
python -m ruff check apps/api tests
```

Full visual/mobile/browser/cloud Firebase acceptance has not run. The complete requested
product remains unfinished; `CURRENT-STATUS.md` records the remaining scope. No interim
package is being represented as the user's final requested delivery.
