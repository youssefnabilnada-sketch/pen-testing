# Full-stack acceptance — NOT EXECUTED in this environment

Docker/Redis/PostgreSQL services were unavailable. Browser observation was rejected by environment security policy. Do not infer this gate passed from unit tests.

Follow README's local fixture workflow, recording screenshots/logs at each step. Test both a desktop and a narrow mobile viewport.

| Steps | Acceptance |
|---|---|
| 1–4 | Compose services healthy, migrations complete, landing renders, customer registers/verifies email, organization created |
| 5–7 | Fixture origin added; correct file challenge succeeds, incorrect/expired challenge fails; exact GET / scope accepted |
| 8–10 | Persisted job moves through actual worker stages; expected 6 observations on insecure HTTP fixture; no fabricated progress |
| 11–13 | Findings visible, fallback explanation labeled, PDF downloadable by correct tenant only |
| 14–18 | Remediation request, distinct platform admin review, formal scope/price quotation, customer acceptance; no payment transaction |
| 19–20 | Engineer assignment and valid task transitions; approved change only to local fixture config |
| 21–23 | Recorded change evidence, customer approval, new explicit authorization and complete-profile retest after cooldown; five response-configuration observations resolve, HTTP remains open; new immutable report |
| 24–25 | Second tenant cannot read assets/findings/reports/messages; feature state and interface show payment processing disabled |

Also stop a worker mid-job, verify stale-job recovery, revoke ownership during an assessment, pause globally and observe bounded cancellation. Check service-health output against actual stopped services. Confirm scanner containers cannot reach public sites or unauthorized internal destinations in this local profile. Add automated full-stack orchestration only when the deployed stack can be executed and validated.

Also validate intelligence-worker official-source egress, source retry/checkpoint retention, scheduler restart recovery, approved knowledge updates, two-tenant inventory isolation and the full comparison/closure gates on a real Compose deployment. These checks are NOT executed here.
