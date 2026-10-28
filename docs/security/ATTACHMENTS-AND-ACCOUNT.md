# Bounded evidence storage and account lifecycle

Attachments use database text storage with a 256 KiB UTF-8 byte limit and a 20-file
per-parent quota. The HTTP envelope is limited to 2 MiB before JSON parsing. PostgreSQL
parent-row locks serialize quota checks; concurrent PostgreSQL verification remains
outstanding. Listing selects metadata only. Downloads always recheck current membership,
parent association and private-file permission, and return no-store, nosniff and an
attachment disposition. No public URLs or customer-controlled disk paths are created.
Only simple ASCII filenames ending txt/log/csv/md are accepted. Executables, archives,
PDFs and images are deliberately unsupported. There is no malware-scanning claim.
Do not place secrets in evidence. Downloaded text is untrusted and is never rendered or
executed by AEGIS. External programs may interpret text differently.

Deleting removes the live database content and retains an audit event, not the content.
Backup retention still applies; this is not cryptographic erasure. Database backup and
restore policy must include attachments. No S3 integration is needed for this limited
file size/type scope; large binary storage remains unimplemented.

Notification preferences and read receipts are personal and checked against current
workspace membership. Hiding a category does not delete alerts or disable monitoring.
The former shared read flag is retained for schema compatibility but no longer controls
any individual's read state. Existing alerts appear unread until that user acknowledges
them. Preferences control in-app visibility only, not email or push delivery.

Profile updates cannot change email, identity or another user's account. Password change,
sign-out-all and account deactivation require current-password confirmation and a fresh
authenticator/recovery code if MFA is enabled. All sessions and pending account email
tokens are revoked. Account deactivation retains audit and tenant evidence, rejects
organization owners and platform administrators, and has no self-service reactivation.
The legacy unconfirmed deactivation endpoint returns a refusal with guidance to the new
flow. Organization creation and lifecycle mutations lock the user row to serialize
ownership creation against deactivation. Actual PostgreSQL race tests remain required.

Ownership transfer now requires explicit confirmation, a matching administrator email,
password and optional MFA. Both users and the organization are locked; the former owner
is demoted to administrator in the same transaction. Real PostgreSQL concurrent transfers
remain untested. Email changes, data-erasure automation, generic step-up on deployment
approval, and full production acceptance are still outstanding. No production changes
or public assessments were performed during this implementation.
