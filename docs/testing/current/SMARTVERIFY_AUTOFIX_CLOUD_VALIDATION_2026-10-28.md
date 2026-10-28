# AEGIS Security Cloud — SmartVerify / AutoFix and cloud acceptance checkpoint

**Status: DEVELOPMENT — NOT VALIDATED FOR PUBLIC PRODUCTION RELEASE.**

## Changes in this checkpoint

1. AutoFix staging proof now requires a complete, exact match between the recorded assessment's paths and the separately authorized baseline paths; missing, extra or mismatched paths are rejected rather than treated as clean proof.
2. The staging evaluator rejects contradictory evidence (`executed` and `not_performed` for the same rule), missing or malformed coverage metadata and duplicate baseline paths.
3. Pre-deployment CI now requires **eight successful jobs**: full backend, frontend tests/build, real PostgreSQL migration round-trip, PostgreSQL/Redis integration including Cloudflare SmartVerify and AutoFix recovery API tests, desktop/mobile Health browser, desktop/mobile production-build smoke browser, separate-process Next/FastAPI/Celery/PostgreSQL/Redis/email fixture, and real WordPress runtime. Skipped/missing/failing jobs fail the gate.
4. Added `scripts/verify_cloud_staging.py`, an opt-in **read-only** HTTPS probe of two explicitly supplied staging endpoints. It checks homepage and security header, API database health/payment-disabled settings, and API `/ready` status. It does not modify external sites or prove production safety. Strict HTTPS origin checks and no redirects.
5. No payment, pricing, conversational assistant, auto-merge or production mutation was enabled.

## Actual checks executed in this runtime

| Check | Outcome | Scope and limits |
|---|---|---|
| `PYTHONPATH=apps/api python -m unittest discover -s tests -p 'test_*unit.py' -q` | **84 passed** | Isolated Python contract/unit tests; not full backend |
| PHP syntax and `php tests/wordpress_contract.php` | **Passed** | Plugin syntax/contract only, NOT WordPress runtime |
| SQLite Alembic upgrade → downgrade → upgrade | **Passed**, revision `017_evidence_legal_holds` | SQLite, NOT PostgreSQL |
| YAML workflow parse and required CI dependencies | **Passed** | Configuration syntax, NOT actual GitHub run |
| Python `compileall`, `git diff --check` | **Passed** | Syntax/whitespace, not functionality |
| Selected full-stack `pytest` attempt | **BLOCKED before collection** | Import of `celery` failed in `tests/conftest.py` |
| pip package installation | **BLOCKED** | Package registry DNS/network unavailable in current runtime |
| PostgreSQL/Redis integration | **NOT RUN** | PostgreSQL and Redis executables/services unavailable here |
| Frontend `npm test`, Next production build, Chromium browser | **NOT RUN** | `apps/web/node_modules` unavailable; no dependency installation network |
| Real WordPress runtime | **NOT RUN** | PHP mysqli/MySQL runtime unavailable; contract above is not sufficient |
| Cloudflare live and Cloud staging smoke | **NOT RUN** | No explicitly authorized staging endpoints / provider credentials available in this environment |

## To verify the full stack on isolated, owned infrastructure

1. Transfer the entire latest ZIP to a **private** GitHub repository (do not overwrite an older unrelated/default repository or publish credentials). Preserve Git history via the supplied bundle.
2. Run `.github/workflows/ci.yml` and require the `predeploy-ci-evidence` job to succeed. Review the *actual* job logs and uploaded JUnit artifacts; fix all failures. This CI covers automated regression and selected controlled browser journeys but does **not** cover every manual customer flow.
3. Deploy a dedicated staging stack with API, Celery worker/beat, managed PostgreSQL and Redis, web frontend, test Firebase identity, controlled SMTP and object storage. Keep live customer sites/scanning disabled. Set real secrets only in the hosting providers' secret managers, not in the ZIP, repo or chat.
4. From an authorized environment with HTTPS access, set `AEGIS_STAGING_WEB_URL` and `AEGIS_STAGING_API_URL` to distinct actual HTTPS origins, then run `python scripts/verify_cloud_staging.py`. This is a read-only smoke, NOT full acceptance.
5. Conduct end-to-end user onboarding, SmartVerify through each configured provider, explicit scan consent, scan, AutoFix approval, staging preview/retests, rollback, customer isolation, WordPress real runtime, delivery of email, data backup+restore drills, MFA, and monitoring in the staging deployment. Record dates, versions, screenshots and test outcomes.
6. Only after successful checks, a security/privacy review, production configuration/backup verification and an authorized launch decision may this checkpoint be considered for public release.

## Known limitations that remain genuine implementation work

- Cloudflare TXT proof is implemented with a bounded create-only flow and fixture-tested; production API authorization and DNS propagation have not been verified here. Other providers' one-click integration is not complete.
- AutoFix currently supports limited deterministic configuration patches and local backup/restore. Full application staging and approved deployment-specific rollback are NOT proved. Do not claim universal AI repairs or remote rollback.
- Browser coverage is not the complete scan/AutoFix/agency/Launch/CRM/WordPress experience.
- Web and API hosting are not deployed or tested by this chat. A connected GitHub repository visible here contains an older AEGIS 0.2 checkpoint; it was **not** overwritten or used to claim latest CI results.

**Non-negotiable defaults:** payments/pricing off, assistant disabled pending validation, separate permissions for proof vs scanning vs modifying source, least privilege, no automatic production changes and no unauthorized tests.
