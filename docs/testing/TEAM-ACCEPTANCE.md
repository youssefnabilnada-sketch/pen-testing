# Team invitation acceptance criteria

Implement before marking complete: owner/admin creates a 48-hour invitation; email
transport failure rolls back; duplicate active invitations are refused; recipient
must explicitly accept while signed in with the exact verified email. IDs alone
grant no access. Pending, expired, accepted and revoked states persist. Cross-tenant
listing/revocation is forbidden. Only owner may grant/manage admin roles; no route
may change/remove the owner. Removing membership takes effect on the next request.
UI must expose incoming invitations even before the user has a workspace, show errors,
and recover pending invitations after reload. Tests cover recipient mismatch, expiry,
replay, mail failure, role escalation, revocation and tenant isolation.
