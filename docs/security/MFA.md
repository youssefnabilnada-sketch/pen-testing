# Optional authenticator protection

Migration `006_mfa` adds encrypted TOTP seeds and hashed one-use recovery codes.
Enrollment and disable require the current AEGIS password. Enrollment also requires
verified email, confirmation from the same session within ten minutes, and a valid code.
Confirmation revokes other sessions; disable revokes all sessions. Password reset does
not remove MFA. Both password and linked Firebase login enforce the second factor. Linking and unlinking an identity also require a fresh factor when MFA is enabled.

Set `MFA_ENCRYPTION_KEY` in the API's private server environment. Generate it there:

```sh
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Never put this value in frontend variables, Git, tickets, or chat. Back it up separately
from the database. Replacing it without re-encrypting existing seeds breaks TOTP login;
there is no automatic rotation facility yet. Offline recovery codes remain usable with
the account password if the key is unavailable. There is no support bypass endpoint.
Without a valid configured key, enrollment is unavailable and existing TOTP protection
fails closed. This setting does not enable paid Firebase MFA or SMS.

The Account security panel offers manual setup-key entry in a time-based authenticator,
confirmation, one-time display of recovery codes, and disable/sign-out. It does not
persist secrets to browser storage. API responses must remain over HTTPS in deployment.
Codes are accepted in a one-step clock window and each counter can be consumed once.
Wait for the next code after enrollment before using that authenticator to sign in.

Limitations: no QR rendering, WebAuthn, enforced organization-wide enrollment, or separate
step-up authorization for other sensitive actions. PostgreSQL race testing, real-device
usability and cloud Firebase login acceptance are outstanding. This is not a claim of
full authentication hardening or production readiness.
