# Attachment acceptance
Support and remediation records accept bounded UTF-8 text evidence (txt/log/csv/md),
not arbitrary executables, archives, active documents or images. Maximum 256 KiB/file,
20 attachments/record. Persist content with relational foreign keys; never use customer
filenames as filesystem paths. Only authenticated, authorized members can download.
Internal support files are staff-only; internal remediation files require owner/admin/
engineer. Viewers cannot upload/delete. Check permission on every operation including
guessed IDs; staff routes require explicit platform administrator access. Downloads use
attachment disposition, nosniff, no-store. Audit upload/download/delete. Closed records
reject upload. Client cannot broaden visibility or change owner. Tests cover exact byte
roundtrip, invalid text/name/size/type, quota, private files, cross-tenant access, role
restrictions, deletion and database upgrade/downgrade. UI must show failures and never
claim malware scanning. No external storage credentials required for this bounded scope.
