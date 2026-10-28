# Explicit paths — implementation in progress

API consent supports up to three simple exact paths; the transport validates scope,
worker rechecks consent before each request and performs no redirect following/crawl.
Findings are keyed per path; omitted paths cannot be resolved by a root-only retest.
25 focused tests passed (multipath-initial.log), including two-path worker persistence.
This is NOT completed: customer path-selection UI, multipath explanation qualification,
full retest/report tests, complete regression and end-to-end verification remain outstanding.
Repository connectors, deployment verification and browser acceptance are not implemented
by this change. Do not deliver as final. No public-target assessments were performed.

Follow-up: customer authorization form now submits explicitly selected paths and resets
consent when edited. Deterministic explanations recognize path-qualified rule IDs. Added
omitted-path unverified comparison and pre-DNS out-of-scope rejection tests.
Executed: 24 focused backend tests passed (multipath-followup.log); 50 existing frontend
component tests passed (multipath-ui.log); TypeScript and configured Ruff checks passed.
The first frontend command used an invalid redirected log path; corrected command passed.
Full multipath-specific UI acceptance, full regression and browser review remain outstanding.


## 2026-10-26 follow-up
Retest path consent is now connected in UI and API. Narrowed baseline scope is rejected. Mixed-path resolved/unresolved results and PDF access were integration-tested. Cancellation, timeout and changed scope were tested without committing partial findings. Qualified detector explanations support hyphenated catalog IDs. Automatic crawling remains unimplemented. See IMPLEMENTATION_STATUS.md and current execution logs; this document is not a completion claim.
