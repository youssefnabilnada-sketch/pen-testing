# 0.4 execution evidence

Backend: 84 passed, 1 Starlette/httpx deprecation warning, 34.31 seconds. Exit 0.
Measured backend statement coverage: 89.526687%.
Command: PYTHONPATH=apps/api pytest tests -q --cov=aegis --cov-report=term --cov-report=json:docs/testing/coverage-0.4.json
See backend-0.4.log and coverage-0.4.json.

Frontend after dependency fix: 14 tests across 5 files passed, 1.65s, exit 0.
Commands: npm test && npm run typecheck && npm run build (apps/web).
TypeScript and Next 15.5.28 production build passed. /console first-load JS 122 kB;
this is a build measurement, not a measured browser latency claim.
Ruff and git diff --check passed. pip check found no broken dependencies.

Audits: npm audit --omit=dev originally found 4 high transitive findings; patched
@grpc/grpc-js with override 1.14.6, reran tests/typecheck/build and audit: zero known
production npm vulnerabilities. pip-audit originally found vulnerabilities in the
pip 25.0.1 tool itself; upgraded to 26.2.2 and reran: no known vulnerabilities.
Reports: npm-audit-0.4.json, python-audit-0.4.json. Audits are point-in-time results.

| Module | Implemented | Tests run | Result | Remaining issues |
|---|---|---|---|---|
| Authentication | Local + Firebase UI/API | foundation, firebase_identity, firebase-client, firebase panel | Pass deterministic | Live Google consent, email and cloud revocation not tested |
| Organizations | Existing | foundation + new identity no-grant tests | Pass | Existing invitation limits |
| Verification | Existing 0.3 guide | onboarding, safety | Pass | No hosting OAuth |
| Assessments | Existing safe profile | assessment, queue, local fixture | Pass | Docker/PG/Redis full runtime not run here |
| Findings | Existing | assessment, regression | Pass | Root-response scope only |
| AI reporting | Deterministic | intelligence/monitoring tests | Pass | No external LLM |
| PDF reports | Existing | assessment/local fixture | Pass | No new visual review |
| Remediation | Engineer managed | remediation/onboarding/monitoring | Pass | No automatic tested patches or deployment |
| Administration | Existing | permission/control regression | Pass | Previous limitations remain |
| UI/UX | Updated identity controls | 14 component/SDK-adapter tests + build | Pass | Desktop/mobile visual acceptance not run |
| Full real cloud E2E | No | Not executed | Blocked | Server identity credentials and manual consent required |

Testing uses controlled local fixtures/mocked identities. The Firebase Admin SDK is
installed, and SDK invocation/exception contracts are tested; real Google signature
and account checks against the user's project were not executed. No account created
in Firebase by our tests. No public website scanning or public deployment performed.
Payments remain disabled. This is a local development checkpoint, not a final release.
