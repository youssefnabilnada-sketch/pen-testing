# Remediation selection and browsing — 26 October 2026

Implemented critical-only, critical/high and all-eligible engineering review requests.
Existing tickets are reused; exclusions apply to individual and bulk requests. Both creation
paths acquire the same asset lock. PostgreSQL concurrency remains unverified.
Customer remediation pages now browse beyond 100 records and filter by status. Refresh
sequence checks prevent an older response overwriting a newer workspace/page refresh.

Executed evidence:
- `python -m pytest tests -q --cov=aegis --cov-report=json:docs/testing/selection-coverage.json --junitxml=docs/testing/selection-full-backend.xml`: 166 passed, 1 skipped, 0 failures/errors, 83.184 seconds.
- `npm --prefix apps/web test -- --reporter=default --reporter=junit --outputFile=../../docs/testing/selection-final-frontend.xml`: 49 passed, 0 failures/errors; JUnit 8.784 seconds. JUnit is authoritative; redirected text output lacks its final footer.
- Coverage: 2868/3131 statements, 91.60012775471095%, configured exclusions.
- `npm --prefix apps/web run build`: completed compilation, typecheck and prerender; selection-build.log.
- Ruff configured checks and git diff --check passed.
- Targeted selection/onboarding browser API suite: 6 passed, selection-browser.xml.

No new dependencies, public assessments, deployment or payments. No browser visual test
was performed. Full original requirements, actual Firebase/cloud integration and deployed
acceptance remain incomplete; this is not a final release. The Redis skip was separately
verified in the previous integration; Redis tests were not repeated for these UI/API changes.
