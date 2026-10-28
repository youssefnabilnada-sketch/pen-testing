# Support acceptance
Authenticated workspace members can read their tickets; owner/admin/analyst/engineer
can create and reply. Viewers cannot mutate. Platform staff use explicit admin routes,
may reply and add private notes; private notes never appear in customer routes even
for a staff user who is also a customer. Tickets persist status and timestamps, support
pagination, have append-only messages and audit events. Closed tickets reject replies
until explicitly reopened. Tests cover cross-tenant IDs, staff permissions, notes,
status transitions, input validation and UI errors. Attachments are a separate gate.
