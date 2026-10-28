# Permitted-window verification — 2026-10-26

Implemented recurring daily UTC consent windows, persisted in authorization scope and
displayed in schedule status. Scheduler defers before ownership verification/queueing;
API enqueue, worker checkpoints, and the pinned transport enforce current consent.
The transport rechecks after DNS resolution and before HTTP dispatch. A ten-second
request budget must fit before a restricted closing hour or authorization expiration.
The supported assessment remains one root-response GET; broader paths are not claimed.

Executed focused security/regression suite: **39 passed**, 46.96 seconds
(`windows-security.xml`, `windows-security.log`). Separate real Redis queue fixture:
**2 passed**, 19.40 seconds (`windows-redis.log`). Final frontend component suite:
**39 passed**, 25.74 seconds (`windows-frontend.xml`, `windows-frontend-final.log`).
TypeScript, Ruff and whitespace checks passed. A full optimized Next build passed with
two build workers and fresh generated output (`windows-build.log`); /console first-load
JavaScript was reported as 129 kB. This is bundle size, not a page-latency measurement.

Earlier build attempts encountered a runtime library failure and stale export-directory
cleanup errors. Previous output was retained outside the source tree, not deleted.
An initial window test used a nonexistent single-job endpoint and was corrected to use
the supported organization assessment list. A subsequent assertion expected a raw error
message, but the worker deliberately redacts errors: the corrected test verifies failed
state and zero transport calls. The monitoring UI contract test was updated for the two
new UTC fields and rerun. No failing result is being represented as a pass.

Final full backend suite: **130 passed, 1 skipped**, zero failures/errors, JUnit elapsed
**285.860 seconds** (`windows-final-backend.xml`). Measured line coverage is
**90.70657848938392%** (`windows-final-coverage.json`). The separate two-test Redis run
covers the queue integration skipped by the default suite. Existing evidence remains
historically separate.
Tests do not include public targets, real Firebase sign-in, PostgreSQL races or browser
visual/accessibility acceptance. These remain release blockers together with the other
unimplemented requirements in `CURRENT-STATUS.md`.
