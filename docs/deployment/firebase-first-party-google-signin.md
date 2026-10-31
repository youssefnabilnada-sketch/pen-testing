# AEGIS — first-party Firebase Google OAuth helper (iOS Safari)
The public website is hosted on Vercel, while Google sign-in uses a Firebase OAuth helper. Safari can lose OAuth initial state across a third-party helper origin. Firebase's recommended reverse proxy solves the cross-origin helper problem, but **must only be activated after the Google OAuth client accepts the new redirect URI**.

Source: https://firebase.google.com/docs/auth/web/redirect-best-practices

## Prerequisites (manual; do not skip)
1. In Firebase Console > Authentication > Settings > Authorized domains, confirm `aegis-pentest-eg.vercel.app`.
2. In Google Cloud Console, select the OAuth 2.0 **Web application client used by the Firebase Google provider** (Credentials). Add `https://aegis-pentest-eg.vercel.app/__/auth/handler` under Authorized redirect URIs. Preserve existing redirect URIs and authorized JavaScript origins.
3. If required by the OAuth client, ensure `https://aegis-pentest-eg.vercel.app` is an authorized JavaScript origin.
4. Check Firebase Authentication > Sign-in method > Google is enabled.
5. Don't paste any OAuth client secret, token or Firebase service-account credentials into chat.

## Deployment (only after prerequisites)
Set **both** Vercel Production environment variables:
- `NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY=true`
- `NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID=<exact Firebase projectId from the existing production /api/auth/firebase/config response>`

Redeploy the reviewed production commit on Vercel. This does **not** require changing Oracle, PostgreSQL, Redis or backend credentials. These vars are public configuration, not secrets.

When enabled and only on `aegis-pentest-eg.vercel.app`, the client uses that host as `authDomain`; the Vercel server transparently proxies the fixed set of Firebase auth helpers to the exact allowlisted Firebase Hosting project. AEGIS session cookies, CSRF and bearer headers are stripped, and response cookies are never forwarded.

## Verification and rollback
1. Verify `https://aegis-pentest-eg.vercel.app/__/auth/iframe` is a served helper and not a redirect to `firebaseapp.com`.
2. Run real Google Register -> Recovery password -> select Google account -> create AEGIS workspace and then Google Login on iPhone Safari in a clean browser session; also test desktop and existing AEGIS password login.
3. Confirm GET `/api/auth/me` without a session still returns 401 and cross-tenant ownership rules are unchanged.
4. If Google sign-in fails, **roll back by disabling** `NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY`, redeploy the previous known-good frontend build, and inspect OAuth client settings / Firebase errors; do not relax Google/Firebase allowlists.
