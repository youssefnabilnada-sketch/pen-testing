# AEGIS 0.1 stabilization source

Current recovered source: 236 backend tests passed, 2 opt-in tests skipped in the default run; those integration checks passed separately in the real Redis/native runtime runner (3 selected tests passed). Measured backend statement coverage: 91.95%. Frontend: 59 component tests passed; TypeScript and production build passed.

Evidence and exact limitations: docs/testing/VERIFIED-0.1-RECOVERY.md. This is not a production-approved final release. Real PostgreSQL integration, end-to-end Firebase application sign-in and browser acceptance remain unverified. GitHub live verification is deferred at the user's request. Expansion modules are planned for 0.2. Payments and conversational AI remain disabled.

Authenticated Firebase project access and live web SDK configuration matching have now been verified (firebase-live-project-check.json). This does not establish successful application sign-in or deployed backend integration.
