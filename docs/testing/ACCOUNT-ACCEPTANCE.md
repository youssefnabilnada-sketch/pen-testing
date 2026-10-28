# Account lifecycle acceptance
An authenticated user can update their own display name, change their password with
current-password confirmation (plus fresh factor if enabled), revoke all sessions, or
deactivate their account with explicit consent and the same reauthentication. Deactivation
must refuse any organization owner and platform administrators; it must revoke sessions
and pending email tokens and never remove tenant evidence or audit records. It is not
data erasure. Ownership transfer requires current-owner password/factor confirmation, an existing active
verified administrator, matching recipient email and explicit consent. Promote the
recipient and demote the former owner atomically with audit. Reject outsiders, nonowners,
stale membership, unverified/inactive targets and mismatched confirmation.
Display names are bounded text, rendered as text; emails and identity bindings cannot be
changed through the profile endpoint. Tests cover wrong password, MFA, revoked sessions,
inactive login/reset, last-owner refusal, non-owner success, and foreign-ID attempts.
