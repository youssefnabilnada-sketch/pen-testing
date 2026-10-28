# Executed integration evidence — 26 October 2026

This is an engineering test record, not final acceptance of the master specification.

| Feature / test identifier | Type and command | Expected | Actual | Result |
|---|---|---|---|---|
| Complete backend suite | `python -m pytest tests -q --cov=aegis --cov-report=json:docs/testing/integrated-final-coverage.json --junitxml=docs/testing/integrated-final-backend.xml` | No failures | 163 passed, 1 skipped; 84.533s JUnit; 0 failures/errors | Pass tested scope |
| Detector gates/parser, finding browser, provider boundary | `python -m pytest tests/test_detectors.py tests/test_finding_browser.py tests/test_ai_provider.py -q` | Activation/retest/tenant/fallback invariants | 31 passed before final combined regression | Pass |
| Real Redis coordination | `python scripts/test-with-redis.py` with recorded runtime Redis binary/lib paths | Actual broker/coordination behavior | 2 passed, 3.83s | Pass |
| Frontend components | `npm --prefix apps/web test -- --reporter=default --reporter=junit --outputFile=../../docs/testing/integrated-final-frontend.xml` | UI interaction tests pass | 45 passed, 18 files, 5.06s reported | Pass |
| Types | `npm --prefix apps/web run typecheck` | No TypeScript errors | Exit 0; also typechecked in build | Pass |
| Production frontend build | `NEXT_TELEMETRY_DISABLED=1 npm --prefix apps/web run build` | Compiles/prerenders | Exit 0; console 130kB first-load JS | Pass build only |
| Python static checks | `python -m ruff check apps/api tests` | Configured rule subset passes | All checks passed | Pass configured subset |
| Patch hygiene | `git diff --check` | No whitespace errors | Exit 0 | Pass |

Coverage: **2842 / 3104 Python statements, 91.55927835051547%** under configured
coverage exclusions. This is not security certification or browser coverage.

Raw evidence: `integrated-final-backend.xml/log`, `integrated-final-coverage.json`,
`integrated-final-frontend.xml/log`, `integrated-redis.log`, `integrated-build.log`.
The default-suite skipped Redis test was run separately using the real Redis harness.
Older `operations-*`, `ai-*`, `detectors-*` records are incremental evidence, not the
latest aggregate. Tests use isolated local fixtures and mocked advisory/provider responses.
No public website or live AI provider was assessed/contacted for this work.

Backend tests include tenant restrictions; source update/retry/dedup; fixture approvals;
full supported-profile regression outcomes; attachments/account/MFA; scheduling windows;
recovery preserving unverified state; history/page filtering and constrained model output.
New UI tests cover explicit detector approval/disable, admin pagination/errors, finding
pagination/history, viewer restrictions and remediation request callbacks.

Remaining mandatory gates: actual Firebase/Google/SMTP, PostgreSQL races and backup/restore,
full deployed services, browser keyboard/mobile/accessibility, performance beyond build size,
independent security review and the still-unimplemented original requirements in CURRENT-STATUS.md.
Browser screenshots and live-provider success are not claimed. No final release is approved.
