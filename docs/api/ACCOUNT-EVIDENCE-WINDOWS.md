# Account, evidence and scheduling additions

All listed routes require a valid session. Mutations additionally require the session's
CSRF header. JSON contracts are exported in `openapi.json` and served at `/docs`.

| Route | Behavior |
|---|---|
| GET/PATCH `/auth/account` | Read own profile; update own display name |
| POST `/auth/account/password` | Confirm current password/factor, change password and revoke sessions/tokens |
| POST `/auth/account/sign-out-all` | Confirm password/factor and revoke sessions/tokens |
| POST `/auth/account/deactivate` | Explicit confirmation; owner/admin guards; retain audit/evidence |
| POST `/organizations/{org}/transfer-ownership` | Current owner transfers to a verified existing administrator with password/factor and email confirmation |
| GET/PUT `/organizations/{org}/notification-preferences` | Personal enabled in-app categories; no effect on teammates |
| POST `/notifications/{id}/read` | Idempotent personal read receipt |
| GET/POST `/files/{kind}/{target}` | List metadata or upload bounded text evidence |
| GET/DELETE `/files/{kind}/{target}/{id}` | Reauthorize download or deletion |

Attachment kind is `support`, `staff-support`, or `remediation`. Staff support requires
platform-administrator permission; ordinary routes never use superadmin to bypass tenant
membership. Upload JSON contains `filename`, UTF-8 `content`, and optional `internal`.
The metadata response contains id, filename, size, visibility and creation timestamp.
Downloads are octet-stream attachments, not JSON. Missing/private file IDs return 404;
foreign-workspace access is refused before retrieving content. No public file URLs exist.

`POST /assets/{asset_id}/schedule` also accepts `start_hour_utc` (0–23) and
`end_hour_utc` (1–24), start strictly less than end. The consent record stores
`daily_window_utc`; no implicit rollover through midnight is supported. The default
0–24 permits any hour during the existing authorization period. Schedule status can be
`waiting_window`, and `next_due` identifies the next permitted dispatch check. The actual
worker and transport recheck consent before network requests. A skipped/failed assessment
never means the asset is secure or a remediation verified.

Upgrade through `009_profile` before starting API workers on this source. The changes
do not add binary-storage requirements or Firebase service privileges.
