# Personal notification state acceptance
Each workspace member, including a viewer, can choose which of the five existing in-app
alert kinds appears in their own notification list. Preferences must not change stored
observations, scheduler behavior, or other members' feeds. Default is all categories.
Read markers are per user, not shared workspace state. Repeated mark-read is idempotent;
non-members are rejected and no client can choose a different user's identity. Existing
shared read flags cannot establish which individual read an alert, so migration leaves
individual alerts unread. Tests cover defaults, validation, personal filtering,
cross-tenant denial, independent read state and persisted settings. No email delivery
is claimed by these settings; this is explicitly an in-app notification preference.
