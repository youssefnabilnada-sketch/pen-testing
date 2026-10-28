# 0.3 execution results

Backend command: `PYTHONPATH=apps/api pytest tests -q --cov=aegis --cov-report=term --cov-report=json:docs/testing/coverage-0.3.json`
Actual: 80 passed, one Starlette/httpx deprecation warning, 65.50 seconds, exit 0.
Measured statement coverage: 88.786008%. See backend-0.3.log and coverage-0.3.json.
Frontend: typecheck passed, 9 Vitest tests passed, Next production build passed.
See FRONTEND-0.3.md. No browser visual evidence for this version.

| Module | Implemented | Tests | Result | Remaining |
|---|---|---|---|---|
| Authentication | Existing + optional Firebase API | foundation, firebase_identity | Pass in fixtures | Firebase frontend, live SDK/cloud, MFA |
| Organization management | Existing | foundation, tenant tests | Pass | Previous invitation limits remain |
| Ownership | Improved guide + GitHub prefilled file | onboarding, safety | Pass | OAuth/hosting connectors absent |
| Assessment | Existing | assessment, queue, live local fixture | Pass | Full Docker queue not tested here |
| Findings | Existing | assessment, regression | Pass | Original coverage limitations |
| AI reporting | Deterministic existing | intelligence, monitoring | Pass | No external LLM |
| PDF | Existing | assessment, local fixture | Pass | No new visual review |
| Remediation | Existing + batch engineer review | remediation, onboarding, monitoring | Pass | No automatic patches/deployment |
| Admin | Existing | foundation, intelligence | Pass | Original limitations |
| UI | Partial update | 9 component tests + TypeScript/build | Pass | Desktop/mobile visual and browser E2E blocked/not run |
| Complete cloud E2E | No | Not run | Blocked | Cloud credentials, deployment, browser acceptance |

No public websites assessed by these tests. Fixture observations are isolated test data.
Payments disabled. Not production-ready; suitable only for further local development
and validation. Firebase optional SDK dependencies not installed or audited in this run.
