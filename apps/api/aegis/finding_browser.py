"""Tenant-scoped searchable finding pages and evidence history."""
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select,func,or_,case
from .auth import current,member
from .db import database
from .models import Finding,Asset,FindingHistory
router=APIRouter()
SEVERITIES=('critical','high','medium','low','info')
STATUSES=('new','open','under_review','accepted_risk','false_positive','remediation_requested','in_progress','ready_for_retest','resolved','reopened')

@router.get('/organizations/{org_id}/finding-page')
def page(org_id:str,q:str=Query('',max_length=100),severity:str='',status:str='',sort:str='recent',offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    if severity and severity not in SEVERITIES:raise HTTPException(422,'Unknown severity.')
    if status and status not in STATUSES:raise HTTPException(422,'Unknown finding status.')
    sorts={'recent':Finding.last_observed.desc(),'oldest':Finding.created.asc(),'severity':case({s:i for i,s in enumerate(SEVERITIES)},value=Finding.severity,else_=99).asc()}
    if sort not in sorts:raise HTTPException(422,'Unknown finding sort.')
    conditions=[Finding.org_id==org_id,Asset.org_id==org_id]
    if q:
        escaped=q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        conditions.append(or_(*[field.ilike('%'+escaped+'%',escape='\\') for field in (Finding.title,Finding.rule,Asset.origin)]))
    if severity:conditions.append(Finding.severity==severity)
    if status:conditions.append(Finding.status==status)
    total=db.scalar(select(func.count()).select_from(Finding).join(Asset,Asset.id==Finding.asset_id).where(*conditions))
    rows=db.execute(select(Finding,Asset.origin).join(Asset,Asset.id==Finding.asset_id).where(*conditions).order_by(sorts[sort],Finding.id).offset(offset).limit(limit))
    return {'total':total,'offset':offset,'limit':limit,'items':[{**{k:getattr(f,k) for k in ('id','asset_id','job_id','rule','title','severity','confidence','evidence','remediation','status','last_observed')},'first_observed':f.created,'origin':origin} for f,origin in rows]}

@router.get('/findings/{finding_id}/history')
def history(finding_id:str,offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),u=Depends(current),db=Depends(database)):
    finding=db.get(Finding,finding_id)
    if not finding:raise HTTPException(404,'Finding not found.')
    member(db,u,finding.org_id)
    predicate=FindingHistory.finding_id==finding.id
    return {'total':db.scalar(select(func.count()).select_from(FindingHistory).where(predicate)),
        'items':[{'id':h.id,'status':h.status,'job_id':h.job_id,'created':h.created} for h in db.scalars(select(FindingHistory).where(predicate).order_by(FindingHistory.created.desc(),FindingHistory.id).offset(offset).limit(limit))]}
