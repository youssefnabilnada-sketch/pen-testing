# MFA acceptance
Opt-in TOTP must protect both password and linked Firebase login. Enrollment requires
current password and verified email, expires in ten minutes, and is bound to the current
session. Store the seed encrypted with a separately configured server key. Confirmation
issues ten one-use recovery codes, stores hashes only, and revokes other sessions.
Reject used TOTP counters and recovery-code replay with atomic updates. Rate-limit per
account as well as login caller. Password reset must not remove MFA. Disabling requires
password plus factor and revokes sessions. Missing encryption key must never bypass MFA.
UI shows manual authenticator enrollment and one-time recovery codes without saving to
browser storage. Tests use isolated generated keys and controlled clocks. No real SMS,
external authenticator account or customer identity is used by tests.
