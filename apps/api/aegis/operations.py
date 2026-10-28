"""Read-only, bounded platform operations views; never exposes authentication material."""
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from .auth import current, admin
from .db import database
from .models import Organization, User, Asset, Job, Report, QueueOutbox, AssessmentSchedule, IntelligenceSource
router=APIRouter(prefix='/admin/operations')

@router.get('')
def overview(u=Depends(current),db=Depends(database)):
    admin(u)
    def count(model,*conditions):return db.scalar(select(func.count()).select_from(model).where(*conditions))
    from .ai_provider import provider_state
    now=time.time()
    return {'checked_at':now,'organizations':count(Organization),'users':count(User),
        'assets':count(Asset),'verified_assets':count(Asset,Asset.verified_until>now),
        'jobs':dict(db.execute(select(Job.status,func.count()).group_by(Job.status)).all()),
        'reports':count(Report),'outbox_pending':count(QueueOutbox,QueueOutbox.dispatched.is_(False)),
        'outbox_retrying':count(QueueOutbox,QueueOutbox.dispatched.is_(False),QueueOutbox.attempts>0),
        'schedules':dict(db.execute(select(AssessmentSchedule.status,func.count()).group_by(AssessmentSchedule.status)).all()),
        'sources':[{'key':s.key,'enabled':s.enabled,'last_success':s.last_success,'next_due':s.next_due,'failures':s.failures} for s in db.scalars(select(IntelligenceSource).order_by(IntelligenceSource.key))],
        'storage':'Database-backed snapshots and bounded text attachments; PDFs generated on demand.',
        'ai_mode':provider_state()['mode'],'ai_provider':provider_state()}

@router.get('/records/{kind}')
def records(kind:str,offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),u=Depends(current),db=Depends(database)):
    admin(u)
    models={'organizations':(Organization,('id','name','created')),
        'users':(User,('id','email','display_name','verified','active','superadmin','created')),
        'assets':(Asset,('id','org_id','origin','verified_until','created')),
        'jobs':(Job,('id','org_id','asset_id','status','progress','cancel','created','finished'))}
    if kind not in models:raise HTTPException(404,'Unknown operations record type.')
    model,fields=models[kind]
    total=db.scalar(select(func.count()).select_from(model))
    rows=db.scalars(select(model).order_by(model.created.desc(),model.id).offset(offset).limit(limit))
    return {'total':total,'offset':offset,'limit':limit,'items':[{f:getattr(row,f) for f in fields} for row in rows]}
