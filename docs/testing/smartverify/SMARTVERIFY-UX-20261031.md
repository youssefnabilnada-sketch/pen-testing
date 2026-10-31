# SmartVerify usability upgrade — 2026-10-31

## Source and isolation
- Base: `integration/aegis-oracle-ux-private-20261031`.
- Feature branch: `feature/smartverify-frictionless-ux-20261031`.
- This is a targeted change to the existing Next.js customer console, not a new site.
- No edits to Docker, Oracle, Vercel deployment aliases, Firebase, Brevo, secrets, scanner scope, PostgreSQL schema, Redis or Celery.
- Do not merge or deploy without passing CI, user/browser acceptance and integration-workstream review.

## What actually works in the existing backend
- Exact-origin ownership challenge methods: HTML file, HTML meta tag and DNS TXT.
- Existing WordPress plugin-assisted HTML proof.
- Existing optional Cloudflare one-record TXT publishing with explicit approval and a zone-limited API token.
- Existing GitHub helper that prepares a reviewable file; customer still commits and deploys it.
- Existing bounded, opt-in DNS recheck (three checks, 30 seconds apart).
- Every method ultimately verifies the *published exact website/domain* through the existing server-side verifier. No scan starts as part of verification.

## New user experience
- Premium dark/glass SmartVerify header, three-step progress cues, clear selectable proof cards, responsive layouts, bilingual copy and accessible selected states.
- A guided website-platform picker for WordPress, Shopify, Wix, Squarespace, Cloudflare, Vercel, Netlify, cPanel, Plesk, Git-based deployments, Google Search Console and custom websites.
- Each platform maps to **one of the existing supported proof methods**. Provider selection is advisory; it is not proof of control.
- Google Search Console is explicitly **not** connected via OAuth: proof there does not automatically satisfy AEGIS verification. Do not market it as one-click until a real authorization flow is implemented and validated.
- Shopify/Wix/Squarespace/Vercel/Netlify/cPanel/Plesk are guided methods, not API-based account integrations. Do not display a fake “Connected” status.
- The existing HTML challenge, token download, GitHub-assisted file preparation, WordPress helper, Cloudflare assisted DNS flow and assessment authorization remain intact.

## Tests and release checks
- Frontend provider-guidance unit tests cover all supported platform mappings, Arabic/RTL, misleading-Google-claim prevention.
- Ownership component test verifies method selection creates only a challenge and cannot silently start assessments.
- Required before integration: CI web unit tests + TypeScript + build; desktop/mobile browser smoke; verify ownership against owned WordPress, standard HTML and DNS fixtures; inspect the console on narrow screens.
- Required before marketing actual OAuth/connector support: provider integration implementation, least-privilege scopes, safe consent, exact domain binding, expiry/revocation, error handling, integration and security tests.
- No live customer site was scanned or modified as part of this change.
