"""Fail-closed grant predicate shared by both authorized discovery endpoints.

No database access happens here: callers must expire session state and reload
rows before *each* request and once again before returning results.
"""


def discovery_grant_active(*, authorization, asset, user, asset_id, org_id,
                           expected_origin, expected_scope, now, paused=False):
    return bool(
        authorization is not None
        and asset is not None
        and user is not None
        and user.active
        and authorization.asset_id == asset_id
        and authorization.user_id == user.id
        and asset.id == asset_id
        and asset.org_id == org_id
        and not authorization.revoked
        and authorization.expires > now
        and asset.verified_until > now
        and asset.origin == expected_origin
        and authorization.scope == expected_scope
        and not paused
    )
