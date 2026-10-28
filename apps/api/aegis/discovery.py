"""One authorized root read yields candidates; linked pages are never fetched."""
import time
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel, Field
from copy import deepcopy
from .auth import current,member,audit
from .db import database
from .models import Asset,Authorization,Setting
from .multipath import validate_paths
from . import safety
from .discovery_grants import discovery_grant_active
router=APIRouter(tags=['Authorized page discovery'])

class Links(HTMLParser):
    def __init__(self,origin):
        super().__init__(convert_charrefs=True);self.origin=origin;self.paths=[]
    def handle_starttag(self,tag,attrs):
        if tag!='a' or len(self.paths)>=30:return
        href=dict(attrs).get('href')
        if not href:return
        try:
            if any(c.isspace() or ord(c)<32 for c in href) or any(c in href for c in ('\\','%')):return
            parsed=urlsplit(urljoin(self.origin+'/',href))
            if parsed.query or parsed.username or parsed.password:return
            if safety.canonical_origin(f'{parsed.scheme}://{parsed.netloc}')!=self.origin:return
            path=parsed.path or '/';validate_paths([path])
            if path not in self.paths:self.paths.append(path)
        except ValueError:return

class Consent(BaseModel):
    accepted:bool

class RecursiveConsent(BaseModel):
    accepted: bool
    max_pages: int = Field(default=10, ge=1, le=20, strict=True)
    max_depth: int = Field(default=3, ge=0, le=5, strict=True)
    max_seconds: int = Field(default=20, ge=1, le=30, strict=True)
    prefixes: list[str] = Field(default_factory=lambda: ['/'], min_length=1, max_length=20)
    excluded: list[str] = Field(default_factory=list, max_length=20)
    sitemaps: bool = False

@router.post('/assets/{asset_id}/discover-recursive')
def recursive(asset_id: str, data: RecursiveConsent, u=Depends(current), db=Depends(database)):
    from .crawler import run, safe_path
    a = db.get(Asset, asset_id)
    if not a: raise HTTPException(404, 'Asset not found.')
    member(db, u, a.org_id, roles=['owner', 'admin', 'analyst'])
    if not data.accepted or a.verified_until <= time.time():
        raise HTTPException(403, 'Verified ownership and explicit recursive discovery consent required.')
    try:
        for path in data.prefixes + data.excluded: safe_path(path)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    from .main import throttle
    throttle('page-discovery:' + a.id)
    scope = {'origin': a.origin, 'purpose': 'recursive-discovery', **data.model_dump(exclude={'accepted'})}
    auth = Authorization(asset_id=a.id, user_id=u.id, scope=scope,
                         expires=min(a.verified_until, time.time() + 60))
    db.add(auth); db.flush()
    auth_id, org_id, origin = auth.id, a.org_id, a.origin
    original = deepcopy(scope)
    audit(db, u, 'discovery.recursive_authorized', auth_id, org_id); db.commit()
    def guard():
        db.expire_all()
        active = db.get(Authorization, auth_id)
        asset = db.get(Asset, asset_id)
        paused = db.get(Setting, 'scans_paused')
        user = db.get(type(u), u.id)
        if not discovery_grant_active(
            authorization=active, asset=asset, user=user, asset_id=asset_id,
            org_id=org_id, expected_origin=origin, expected_scope=original,
            now=time.time(), paused=bool(paused and paused.value)
        ):
            raise HTTPException(409, 'Discovery stopped because authorization or operational state changed.')
        member(db, user, org_id, roles=['owner', 'admin', 'analyst'])
    try:
        result = run(origin, **data.model_dump(exclude={'accepted'}), check=guard)
        guard()  # A changed grant cannot be used to publish previously fetched paths.
        auth = db.get(Authorization, auth_id)
        auth.scope = {**original, 'result': result}
        audit(db, u, 'discovery.recursive_completed', auth_id, org_id)
        return {**result, 'authorization_id': auth_id}
    finally:
        auth = db.get(Authorization, auth_id)
        if auth: auth.revoked = True
        db.commit()

@router.get('/assets/{asset_id}/discovery-history')
def history(asset_id: str, u=Depends(current), db=Depends(database)):
    from sqlalchemy import select
    asset = db.get(Asset, asset_id)
    if not asset: raise HTTPException(404, 'Asset not found.')
    member(db, u, asset.org_id)
    rows = db.scalars(select(Authorization).where(
        Authorization.asset_id == asset_id,
        Authorization.scope['purpose'].as_string() == 'recursive-discovery'
    ).order_by(Authorization.created.desc()).limit(20))
    return [{'id': row.id, 'created': row.created, 'scope': row.scope,
             'active': not row.revoked and row.expires > time.time()} for row in rows]

@router.post('/assets/{asset_id}/discover-pages')
def discover(asset_id:str,data:Consent,u=Depends(current),db=Depends(database)):
    a=db.get(Asset,asset_id)
    if not a:raise HTTPException(404,'Asset not found.')
    member(db,u,a.org_id,roles=['owner','admin','analyst'])
    if not data.accepted or a.verified_until<=time.time():raise HTTPException(403,'Verified ownership and explicit root-page discovery consent required.')
    from .main import throttle
    throttle('page-discovery:'+a.id)
    scope={'origin':a.origin,'paths':['/'],'method':'GET','request_limit':1,'timeout_seconds':5,'type':'root-response-configuration','purpose':'link-discovery','window_start':time.time()}
    auth=Authorization(asset_id=a.id,user_id=u.id,scope=scope,expires=min(a.verified_until,time.time()+60))
    db.add(auth);db.flush()
    auth_id, org_id, origin = auth.id, a.org_id, a.origin
    original = deepcopy(scope)
    audit(db,u,'discovery.authorized',auth_id,org_id);db.commit()
    def guard():
        db.expire_all()
        active=db.get(Authorization,auth_id)
        asset=db.get(Asset,asset_id)
        user=db.get(type(u),u.id)
        paused=db.get(Setting,'scans_paused')
        if not discovery_grant_active(
            authorization=active, asset=asset, user=user, asset_id=asset_id,
            org_id=org_id, expected_origin=origin, expected_scope=original,
            now=time.time(), paused=bool(paused and paused.value)
        ):
            raise safety.UnsafeTarget('Discovery authorization is inactive.')
        member(db,user,org_id,roles=['owner','admin','analyst'])
    try:
        with safety.authorization_guard(guard):
            observation=safety.fetch(origin,assessment_scope=original,discovery=True);guard()
        media=next((v.split(';')[0].strip().lower() for k,v in observation.headers if k.lower()=='content-type'),'')
        if observation.status!=200 or media not in ('text/html','application/xhtml+xml'):raise ValueError('Supported HTML required.')
        parser=Links(origin);parser.feed(observation.body.decode('utf-8',errors='replace'));parser.close()
        guard()
        audit(db,u,'discovery.completed',auth_id,org_id)
        return {'paths':parser.paths,'requests_performed':1,'authorization_id':auth_id,'limitations':'Only root HTML, at most 30 candidates. No JavaScript, redirects or linked-page requests. Select up to three paths and authorize a separate assessment.'}
    except (ValueError,OSError) as exc:
        audit(db,u,'discovery.failed',auth_id,org_id)
        raise HTTPException(422,'Discovery could not complete safely. Check verification, HTML response and operational status.') from exc
    finally:
        active = db.get(Authorization, auth_id)
        if active: active.revoked = True
        db.commit()
