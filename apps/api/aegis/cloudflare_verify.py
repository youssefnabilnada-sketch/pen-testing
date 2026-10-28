"""Explicit, bounded Cloudflare TXT ownership-proof publication.

This integration can ONLY create an AEGIS TXT challenge. It cannot modify an
existing DNS record, verify a site on its own, authorize scanning, or grant
editing permissions. Customer-supplied Cloudflare tokens are used for one
request and are never persisted or echoed in errors.
"""
import json
import re
import time
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import select

from .auth import audit, current, member
from .db import database
from .models import Asset, Challenge, Membership

router = APIRouter(tags=['SmartVerify Cloudflare'])
_CLOUDFLARE_API = 'https://api.cloudflare.com/client/v4'
_ZONE_ID = re.compile(r'[0-9a-fA-F]{32}\Z')


class CloudflarePublish(BaseModel):
    zone_id: str = Field(min_length=32, max_length=32)
    api_token: SecretStr = Field(min_length=12, max_length=256)
    confirm_dns_change: bool = False
    mfa_code: str = Field(default='', max_length=64)


def proof(origin: str, challenge: Challenge) -> dict:
    """Only DNS challenges are eligible; never accept a caller-controlled record name/value."""
    if (challenge.method != 'dns' or challenge.consumed or challenge.expires <= time.time()):
        raise HTTPException(409, 'Create a current DNS verification challenge first.')
    host = urlsplit(origin).hostname
    if not host:
        raise HTTPException(422, 'Invalid registered hostname.')
    try:
        hostname = host.encode('idna').decode('ascii').lower().rstrip('.')
    except UnicodeError:
        raise HTTPException(422, 'Invalid registered hostname.') from None
    return {'type': 'TXT', 'name': '_aegis.' + hostname,
            'content': 'aegis=' + challenge.token, 'ttl': 300}


def _cloudflare(method: str, path: str, token: str, *, params=None, payload=None) -> dict:
    """Fixed-origin API; limit bytes *while reading*, never follow redirects or proxies."""
    try:
        with httpx.Client(timeout=httpx.Timeout(8, connect=3),
                          follow_redirects=False, trust_env=False) as client:
            with client.stream(method, _CLOUDFLARE_API + path,
                               headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'},
                               params=params, json=payload) as res:
                if res.status_code < 200 or res.status_code >= 300:
                    raise HTTPException(502, 'Cloudflare rejected the scoped DNS request.')
                declared = res.headers.get('content-length', '')
                if declared.isdecimal() and int(declared) > 65536:
                    raise HTTPException(502, 'Cloudflare returned an oversized DNS response.')
                chunks = []
                total = 0
                for chunk in res.iter_bytes(chunk_size=4096):
                    total += len(chunk)
                    if total > 65536:
                        raise HTTPException(502, 'Cloudflare returned an oversized DNS response.')
                    chunks.append(chunk)
        body = json.loads(b''.join(chunks))
        if not isinstance(body, dict) or body.get('success') is not True:
            raise HTTPException(502, 'Cloudflare could not complete the scoped DNS request.')
        return body
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, TypeError):
        raise HTTPException(502, 'Cloudflare DNS connection failed.') from None


def publish_record(origin: str, challenge: Challenge, zone_id: str, token: str,
                   *, before_write=None) -> dict:
    """Confirm the zone and existing records before a single create-only call."""
    if not _ZONE_ID.fullmatch(zone_id):
        raise HTTPException(422, 'Enter a valid Cloudflare zone ID.')
    expected = proof(origin, challenge)
    zone = _cloudflare('GET', '/zones/' + zone_id, token).get('result')
    if not isinstance(zone, dict) or not isinstance(zone.get('name'), str):
        raise HTTPException(502, 'Cloudflare zone details were incomplete.')
    try:
        zone_name = zone['name'].rstrip('.').encode('idna').decode('ascii').lower()
        hostname = (urlsplit(origin).hostname or '').rstrip('.').encode('idna').decode('ascii').lower()
    except UnicodeError:
        raise HTTPException(502, 'Cloudflare zone hostname was invalid.') from None
    if not (hostname == zone_name or hostname.endswith('.' + zone_name)):
        raise HTTPException(403, 'This Cloudflare zone does not cover the registered website.')

    existing = _cloudflare('GET', '/zones/' + zone_id + '/dns_records', token,
                          params={'type':'TXT', 'name':expected['name'], 'per_page':100})
    records = existing.get('result')
    info = existing.get('result_info')
    if (not isinstance(records, list) or not isinstance(info, dict)
        or type(info.get('total_pages')) is not int
        or not 0 <= info['total_pages'] <= 1):
        raise HTTPException(502, 'Cloudflare record listing could not be fully verified.')
    for row in records:
        if (not isinstance(row, dict) or row.get('type') != 'TXT'
            or not isinstance(row.get('name'), str)
            or row['name'].lower().rstrip('.') != expected['name']
            or not isinstance(row.get('content'), str)):
            raise HTTPException(502, 'Cloudflare returned unexpected DNS records.')
        if row['content'].strip('"') == expected['content']:
            if before_write:
                before_write()  # Revocation must also block an idempotent confirmation.
            return {'published': False, 'already_present': True,
                    'message': 'The existing AEGIS TXT proof matches. Check ownership separately.'}

    # Permission and challenge can be revoked while external API calls are in flight.
    # Revalidate immediately before the only remote DNS mutation.
    if before_write:
        before_write()
    created = _cloudflare('POST', '/zones/' + zone_id + '/dns_records', token,
                         payload={**expected, 'comment':'Temporary AEGIS ownership verification proof'})
    record = created.get('result')
    if (not isinstance(record, dict) or record.get('type') != 'TXT'
        or not isinstance(record.get('name'), str)
        or record['name'].lower().rstrip('.') != expected['name']
        or not isinstance(record.get('content'), str)
        or record['content'].strip('"') != expected['content']):
        raise HTTPException(502, 'Cloudflare record creation could not be confirmed; check DNS before retrying.')
    return {'published': True, 'already_present': False,
            'message': 'TXT proof published. Allow DNS propagation, then check ownership separately.'}


def _scoped_challenge(db, user, asset_id, challenge_id):
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, 'Asset not found.')
    member(db, user, asset.org_id, roles=['owner', 'admin'])
    if not user.verified:
        raise HTTPException(403, 'Email verification required.')
    challenge = db.get(Challenge, challenge_id)
    if not challenge or challenge.asset_id != asset.id:
        raise HTTPException(404, 'Verification challenge not found.')
    return asset, challenge


@router.get('/assets/{asset_id}/challenge/{challenge_id}/cloudflare/preview')
def preview(asset_id: str, challenge_id: str, u=Depends(current), db=Depends(database)):
    asset, challenge = _scoped_challenge(db, u, asset_id, challenge_id)
    return {**proof(asset.origin, challenge), 'requires_confirmation':True,
            'changes': 'Create one TXT record. No other DNS records are modified.',
            'verification_is_separate':True}


@router.post('/assets/{asset_id}/challenge/{challenge_id}/cloudflare/publish')
def publish(asset_id: str, challenge_id: str, data: CloudflarePublish,
            u=Depends(current), db=Depends(database)):
    if not data.confirm_dns_change:
        raise HTTPException(422, 'Confirm the single DNS TXT change before publishing.')
    asset, challenge = _scoped_challenge(db, u, asset_id, challenge_id)
    origin = asset.origin
    proof(origin, challenge)
    from .mfa import enforce
    enforce(db, u, data.mfa_code)

    def revalidate():
        db.refresh(asset)
        db.refresh(challenge)
        if asset.origin != origin or challenge.asset_id != asset.id:
            raise HTTPException(409, 'Website or challenge changed during DNS publication.')
        proof(origin, challenge)
        role = db.scalar(select(Membership.role).where(
            Membership.org_id == asset.org_id, Membership.user_id == u.id).execution_options(populate_existing=True))
        if role not in ('owner', 'admin'):
            raise HTTPException(403, 'Permission was revoked during DNS publication.')

    result = publish_record(origin, challenge, data.zone_id, data.api_token.get_secret_value(),
                            before_write=revalidate)
    audit(db, u, 'ownership.cloudflare_dns_proof_checked' if result['already_present'] else
          'ownership.cloudflare_dns_proof_created', asset.id, asset.org_id)
    db.commit()
    return result
