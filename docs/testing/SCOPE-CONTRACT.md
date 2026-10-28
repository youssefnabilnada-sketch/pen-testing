# Shared scope contract

Acceptance: manual enqueue, recurring/retest enqueue and worker checkpoints must reject
unsupported origins, paths, methods, request budgets and transport timeouts before assessment
traffic. Boolean budgets must not be accepted as integer 1. Rechecking after queue submission
must prevent a changed scope from initiating network traffic. Existing recurring consent
without an explicit method retains its original GET-only semantics.

Implemented shared `require_supported_scope`; window validation also rejects non-object scopes.
This is hardening of the existing root-response profile, not implementation of multi-path crawling.

Executed focused command:
`python -m pytest tests/test_scope_contract.py tests/test_windows.py tests/test_monitoring_regression.py -q --junitxml=docs/testing/scope-contract.xml`
Result: 21 passed in 9.40s. Static Ruff configured subset and git diff checks passed.
Full suite evidence is recorded separately in scope-full.xml/log when complete.
No customer/public target was contacted. Live cloud, browser and broader original scope remain
unimplemented or unverified as recorded in CURRENT-STATUS.md. No final release approved.

Full regression completed: 174 passed, 1 skipped, 81.50 seconds; scope-full.xml/log. No new coverage percentage measured for this change.

Additional queue-boundary regression: changed method, request budget, path and timeout
must fail scheduled/retest enqueue without persisting a Job or QueueOutbox row.
Executed `pytest tests/test_scope_contract.py tests/test_windows.py tests/test_monitoring_regression.py -q`:
25 passed in 11.75s, scope-enqueue.xml/log. This change adds tests only; no new full-suite
coverage percentage or deployment acceptance is claimed.
