"""Independent authorized uptime checks; no security assessment or remediation implied."""
import time
import ssl
from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, update, delete, func
from .auth import current, member, audit
from .db import Session, database
from .models import Asset, Authorization, HealthMonitor, HealthSample, Setting, User
from .multipath import validate_paths
from .worker import celery
from . import safety
from .health_safety import mark_blocked_if_present, dispatch_due_monitors
from .historical_records import asset_origin, authorization_expiry

router=APIRouter(tags=['Website health'])

class MonitorInput(BaseModel):
    accepted: bool
    path: str = '/'
    interval_seconds: int = Field(default=900, ge=300, le=86400, strict=True)
    hours: int = Field(default=24, ge=1, le=24, strict=True)

@router.put('/assets/{asset_id}/health-monitor')
def configure(asset_id: str, data: MonitorInput, u=Depends(current), db=Depends(database)):
    asset=db.scalar(select(Asset).where(Asset.id==asset_id).with_for_update())
    if not asset: raise HTTPException(404,'Asset not found.')
    member(db,u,asset.org_id,roles=['owner','admin','analyst'])
    if not data.accepted or asset.verified_until<=time.time():
        raise HTTPException(403,'Verified ownership and explicit monitoring consent required.')
    try: validate_paths([data.path])
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    row=db.scalar(select(HealthMonitor).where(HealthMonitor.asset_id==asset_id))
    if not row and db.scalar(select(func.count()).select_from(HealthMonitor).where(HealthMonitor.org_id==asset.org_id))>=100:
        raise HTTPException(409,'Workspace monitor limit reached.')
    scope={'origin':asset.origin,'paths':[data.path],'type':'explicit-path-response',
           'method':'GET','request_limit':1,'timeout_seconds':5,'purpose':'health-monitoring',
           'interval_seconds':data.interval_seconds}
    auth=Authorization(asset_id=asset_id,user_id=u.id,scope=scope,expires=min(asset.verified_until,time.time()+data.hours*3600))
    db.add(auth);db.flush()
    if row:
        previous_auth = db.get(Authorization,row.authorization_id)
        if previous_auth: previous_auth.revoked = True
        row.authorization_id=auth.id;row.interval_seconds=data.interval_seconds;row.enabled=True;row.next_due=time.time()
    else:
        row=HealthMonitor(org_id=asset.org_id,asset_id=asset_id,authorization_id=auth.id,
                          interval_seconds=data.interval_seconds,next_due=time.time())
        db.add(row)
    audit(db,u,'health.authorized',asset_id,asset.org_id);db.commit()
    return {'id':row.id,'expires':auth.expires,'interval_seconds':row.interval_seconds}

@router.delete('/health-monitors/{monitor_id}')
def disable(monitor_id: str, u=Depends(current), db=Depends(database)):
    row=db.get(HealthMonitor,monitor_id)
    if not row: raise HTTPException(404,'Monitor not found.')
    member(db,u,row.org_id,roles=['owner','admin','analyst'])
    row.enabled=False
    previous_auth = db.get(Authorization,row.authorization_id)
    if previous_auth: previous_auth.revoked = True
    audit(db,u,'health.disabled',row.id,row.org_id);db.commit()
    return {'enabled':False}

@router.get('/organizations/{org_id}/health-monitors')
def listing(org_id: str, u=Depends(current), db=Depends(database)):
    member(db,u,org_id)
    rows=db.scalars(select(HealthMonitor).where(HealthMonitor.org_id==org_id).order_by(HealthMonitor.created.desc()).limit(100))
    return [{'id':r.id,'asset_id':r.asset_id,'origin':asset_origin(db, Asset, r.asset_id, org_id),
             'enabled':r.enabled,'interval_seconds':r.interval_seconds,'next_due':r.next_due,
             'last_status':r.last_status,'expires':authorization_expiry(db, Authorization, r.authorization_id, r.asset_id)} for r in rows]

@router.get('/health-monitors/{monitor_id}/samples')
def samples(monitor_id: str, u=Depends(current), db=Depends(database)):
    row=db.get(HealthMonitor,monitor_id)
    if not row: raise HTTPException(404,'Monitor not found.')
    member(db,u,row.org_id)
    rows=db.scalars(select(HealthSample).where(HealthSample.monitor_id==monitor_id).order_by(HealthSample.created.desc()).limit(100))
    return [{'id':r.id,'created':r.created,'status':r.status,'http_status':r.http_status,
             'response_ms':r.response_ms,'tls_expires':r.tls_expires,'incident':r.incident,
             'domain_expiration':None} for r in rows]


@router.get('/health-monitors/{monitor_id}/report.pdf')
def health_report(monitor_id: str, u=Depends(current), db=Depends(database)):
    """Recorded samples only; does not calculate an uptime percentage or claim an SLA."""
    monitor = db.get(HealthMonitor, monitor_id)
    if not monitor:
        raise HTTPException(404, 'Monitor not found.')
    member(db, u, monitor.org_id)
    asset = db.get(Asset, monitor.asset_id)
    auth = db.get(Authorization, monitor.authorization_id)
    observations = db.scalars(select(HealthSample).where(
        HealthSample.monitor_id == monitor_id).order_by(HealthSample.created.desc()).limit(100)).all()
    from .reporting import render_health_monitor_pdf
    pdf = render_health_monitor_pdf(monitor, asset.origin if asset else 'unavailable', auth, observations)
    return Response(pdf.getvalue(), media_type='application/pdf',
                    headers={'Cache-Control': 'no-store',
                             'Content-Disposition': 'attachment; filename="aegis-health-observations.pdf"',
                             'X-Content-Type-Options': 'nosniff'})

class Stopped(Exception): pass

@celery.task(name='aegis.health_sample',time_limit=30,soft_time_limit=25)
def sample(monitor_id):
    with Session() as db:
        now=time.time()
        row=db.get(HealthMonitor,monitor_id)
        if not row:return
        claim=db.execute(update(HealthMonitor).where(HealthMonitor.id==monitor_id,
            HealthMonitor.enabled.is_(True),HealthMonitor.next_due<=now).values(next_due=now+row.interval_seconds))
        db.commit()
        if not claim.rowcount:return
        db.refresh(row)
        auth_id=row.authorization_id
        initial_auth=db.get(Authorization,auth_id)
        if initial_auth is None:
            mark_blocked_if_present(db,monitor_id);return
        original=deepcopy(initial_auth.scope)
        previous=row.last_status
        last_sample=db.scalar(select(HealthSample).where(HealthSample.monitor_id==monitor_id).order_by(HealthSample.created.desc()).limit(1))
        previous_expiry=last_sample.tls_expires if last_sample else None
        def guard():
            db.expire_all()
            latest=db.get(HealthMonitor,monitor_id);auth=db.get(Authorization,auth_id)
            if latest is None or auth is None:
                raise Stopped()
            asset=db.get(Asset,latest.asset_id);paused=db.get(Setting,'scans_paused')
            user=db.get(User,auth.user_id)
            if (asset is None or user is None or not latest.enabled
                or latest.authorization_id!=auth_id or auth.revoked
                or auth.expires<=time.time() or asset.verified_until<=time.time()
                or auth.scope!=original or asset.origin!=original['origin']
                or not user.active or (paused and paused.value)):raise Stopped()
            try: member(db,user,latest.org_id,roles=['owner','admin','analyst'])
            except HTTPException as exc: raise Stopped() from exc
        status='unavailable';http_status=None;expires=None;elapsed=None
        try:
            with safety.authorization_guard(guard):
                guard();started=time.monotonic()
                response=safety.fetch(original['origin'],original['paths'][0],assessment_scope=original)
                elapsed=(time.monotonic()-started)*1000
                guard()
            http_status=response.status
            status='up' if 200<=http_status<300 else 'down'
            expires=response.tls.get('expires') if response.tls else None
        except Stopped:
            mark_blocked_if_present(db,monitor_id);return
        except ssl.SSLError:
            status='tls_error'
        except (ValueError,OSError):
            try:guard()
            except Stopped:
                mark_blocked_if_present(db,monitor_id);return
        try:guard()
        except Stopped:
            mark_blocked_if_present(db,monitor_id);return
        incident=status!='up'
        entry=HealthSample(monitor_id=monitor_id,status=status,http_status=http_status,
                           response_ms=elapsed,tls_expires=expires,incident=incident)
        db.add(entry);db.flush();row.last_status=status
        if status!=previous and (incident or previous in ('down','unavailable','tls_error')):
            from .intelligence.service import notify
            notify(db,row.org_id,'health_change','health:'+entry.id,
                   'Website recovered' if status=='up' else 'Website health incident',
                   'Approved endpoint status: '+status+'. Check the health history for evidence.',monitor_id)
        if expires is not None and expires<=now+30*86400:
            from .intelligence.service import notify
            if previous_expiry!=expires or (last_sample and previous_expiry>last_sample.created+30*86400):
                notify(db,row.org_id,'health_change','health-tls:'+monitor_id+':'+str(expires),
                       'TLS certificate expires soon',
                       'The observed certificate expires within 30 days. Renew it and review the next health check.',monitor_id)
        # Bounded history: keep the most recent 1000 samples per monitor.
        old=select(HealthSample.id).where(HealthSample.monitor_id==monitor_id).order_by(HealthSample.created.desc(),HealthSample.id).offset(1000)
        db.execute(delete(HealthSample).where(HealthSample.id.in_(old)))
        db.commit()

@celery.task(name='aegis.health_tick')
def tick():
    with Session() as db:
        ids=list(db.scalars(select(HealthMonitor.id).where(HealthMonitor.enabled.is_(True),HealthMonitor.next_due<=time.time()).limit(20)))
    dispatch_due_monitors(ids, sample.delay)
