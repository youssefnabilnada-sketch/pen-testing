# Executed verification — 2026-10-25

Status: development work preserved; the complete requested product is not finished.
No public deployment or real payment transaction was performed.

## Commands and results

| Check | Command / procedure | Actual result | Evidence |
|---|---|---|---|
| Backend regression | `PYTHONPATH=apps/api python -m pytest tests -q --cov=aegis --cov-report=term --cov-report=json:docs/testing/coverage-current.json` | PASS: 88 tests, 126.54 seconds; 1 upstream Starlette/httpx deprecation warning | backend-current.log |
| Backend line coverage | pytest-cov measured executed source statements | 1,857 / 2,081 = 89.23594425756848%; 224 uncovered | coverage-current.json |
| Frontend components | `npm --prefix apps/web test` | PASS: 16 tests in 6 files, 6.33 seconds | frontend-current.log |
| Static checks | `python -m ruff check apps/api tests` and `git diff --check` | PASS | Executed after code and documentation updates |
| TypeScript | `npm --prefix apps/web run typecheck` | PASS: no type errors | frontend-current.log |
| Production frontend build | `npm --prefix apps/web run build` | PASS: routes generated; console initial JS 123 kB (build estimate, not latency benchmark) | frontend-current.log |
| PDF visual inspection | Render isolated quotation fixture with ReportLab and pdftoppm; inspect rendered page | PASS for that one-page English fixture: readable, no clipping | Automated text checks also in test_remediation_documents.py; not general multilingual layout acceptance |

Node emitted a host configuration warning about `http-proxy`; it did not fail the commands.
No current dependency-audit result is claimed by this report; earlier checkpoint audits
remain historical evidence. Coverage is measured backend line coverage, not proof of
full feature coverage or frontend coverage.

## Feature acceptance evidence

| Module | Implemented | Tests run | Result | Remaining issues |
|---|---|---|---|---|
| Authentication | Partial | Existing auth and Firebase contract tests in full suite | Covered cases PASS | Real Firebase/Google, MFA, lifecycle acceptance outstanding |
| Organization management | Partial | Existing role/tenant tests | Covered cases PASS | Invitations and complete membership lifecycle missing |
| Domain verification | Partial | Ownership/safety fixtures and customer journey | Covered cases PASS | Provider connections and expanded scopes missing |
| Assessment engine | Partial | test_assessment.py, test_journey_reliability.py, test_customer_journey.py | PASS | Root GET only; full Docker/PostgreSQL/Redis concurrency unverified |
| Findings management | Partial | Full-suite normalization/history/regression tests | Covered cases PASS | Broader detector coverage missing |
| AI reporting | Partial | Deterministic explanation/knowledge tests | Covered cases PASS | External/local provider operation not implemented |
| PDF reports | Partial | test_remediation_documents.py and assessment report tests | PASS | All document layouts/languages not visually verified |
| Remediation management | Partial | Evidence approval, quote acceptance, local fixture retest, completion gates | PASS | Real repository patches and deployment absent |
| Admin panel | Partial | Role, quotation, pause and existing operations tests | Covered cases PASS | Full operational console incomplete |
| UI/UX | Partial | 16 component tests, TypeScript, build | PASS for executed checks | Browser, mobile, accessibility acceptance BLOCKED/unexecuted |
| End-to-end workflow | Partial | API + real owned HTTP fixture + Celery in-memory worker | PASS for bounded API journey | Full 25-step browser/Compose/cloud scenario NOT RUN |

The journey creates accounts/workspace, verifies the owned local fixture, runs actual
bounded requests, persists findings, reads a PDF, issues/accepts a quotation, records
a fixture change and reruns the complete supported profile. Exactly three fixture
requests are expected: proof, baseline, retest. The HTTP transport finding remains;
closing the remediation is correctly refused. A separate deterministic HTTPS-response
fixture exercises successful closure. Neither fixture proves a live customer site secure.

The reliability tests verify broker failure retains a queued outbox record, cancellation
prevents later dispatch, stored approval evidence survives retrieval, and another tenant
cannot read it. PDF tests extract actual document text, verify scope/organization/no-payment
wording, exclude internal notes, and block stale or unsupported completion claims.

## Release decision

Suitable for continued local development/testing only. Not cleared for customer pilot,
public deployment or production. See ../../CURRENT-STATUS.md and RELEASE-GATES.md for
the full missing scope. Docker, PostgreSQL/Redis runtime, cloud Firebase, real browser
workflows and independent security review remain unverified here. No screenshots of
the current UI are claimed. Payments remain disabled; quotations are never receipts.
