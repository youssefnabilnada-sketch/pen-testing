"""Tenant-scoped, fail-closed projections of legacy intelligence records.

Old jobs, authorizations, assets and manifests may have been removed or repaired.
Do not turn broken foreign-key references into 500s, cross-tenant metadata
exposure, or apparently active assessment consent.
"""
import time
from ..models import Asset, Advisory, Authorization, Finding, InventoryItem, Job


def inventory_view(db, row, org_id):
    asset = db.get(Asset, row.asset_id)
    asset_id = row.asset_id if asset and asset.org_id == org_id else None
    return {'id': row.id, 'asset_id': asset_id, 'ecosystem': row.ecosystem,
            'package': row.package, 'version': row.version, 'evidence': row.evidence,
            'updated': row.updated, 'asset_available': asset_id is not None}


def impact_view(db, row, org_id):
    item = db.get(InventoryItem, row.inventory_id)
    valid_item = bool(item and item.org_id == org_id)
    asset = db.get(Asset, item.asset_id) if valid_item else None
    advisory = db.get(Advisory, row.advisory_id) if valid_item and asset and asset.org_id == org_id else None
    valid = bool(advisory and asset and asset.org_id == org_id)
    return {'id': row.id, 'asset_id': item.asset_id if valid else None,
            'identifier': advisory.identifier if valid else 'unavailable',
            'advisory_id': row.advisory_id if valid else None,
            'status': row.status if valid else 'unverified',
            'reason': row.reason if valid else 'Referenced inventory or advisory unavailable; no current match claimed.',
            'revision_ids': row.revision_ids if valid else [], 'record_available': valid}


def schedule_view(db, row, org_id, now=None):
    if now is None:
        now = time.time()
    asset = db.get(Asset, row.asset_id)
    valid_asset = bool(asset and asset.org_id == org_id)
    auth = db.get(Authorization, row.authorization_id) if valid_asset else None
    scope = auth.scope if auth and isinstance(auth.scope, dict) else {}
    consent_active = bool(auth and auth.asset_id == row.asset_id and not auth.revoked
                          and auth.expires > now and scope.get('recurring') is True)
    window = scope.get('daily_window_utc') if consent_active else None
    if not (isinstance(window, list) and len(window) == 2
            and all(type(x) is int for x in window) and 0 <= window[0] < window[1] <= 24):
        window = None
    return {'id': row.id, 'asset_id': row.asset_id if valid_asset else None,
            'cadence': row.cadence, 'enabled': row.enabled,
            'authorization_active': consent_active,
            'next_due': row.next_due, 'last_run': row.last_run,
            'status': row.status if consent_active else 'blocked_no_current_consent',
            'on_advisory': row.on_advisory, 'reverify': row.reverify,
            'daily_window_utc': window}


def baseline_paths(db, retest, org_id, remediation):
    """Never display another asset's paths as this remediation's scope."""
    finding = db.get(Finding, remediation.finding_id)
    job = db.get(Job, retest.baseline_job_id)
    if not finding or finding.org_id != org_id or not job or job.org_id != org_id:
        return None
    if job.asset_id != finding.asset_id:
        return None
    auth = db.get(Authorization, job.authorization_id)
    if not auth or auth.asset_id != job.asset_id or not isinstance(auth.scope, dict):
        return None
    paths = auth.scope.get('paths')
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        return None
    return paths[:20]
