"""Safe labels for records whose referenced objects may have been removed.

Historical findings/assessments/monitoring observations may outlive a site or
its authorization. Never dereference an absent relationship or display an
origin associated with a different workspace after inconsistent data imports.
"""


def asset_origin(db, asset_model, asset_id, expected_org_id):
    asset = db.get(asset_model, asset_id) if asset_id else None
    if asset is None or asset.org_id != expected_org_id:
        return 'unavailable'
    return asset.origin


def authorization_expiry(db, authorization_model, authorization_id, expected_asset_id):
    authorization = db.get(authorization_model, authorization_id) if authorization_id else None
    if authorization is None or authorization.asset_id != expected_asset_id:
        return None
    if getattr(authorization, 'revoked', False):
        return None
    return authorization.expires
