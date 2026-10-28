"""Paginated remediation work, with tenant-scoped finding context."""
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy import select,func
from .auth import current,member
from .db import database
from .models import Remediation,Finding
router=APIRouter()

@router.get('/organizations/{org_id}/remediation-page')
def page(org_id:str,status:str='',offset:int=Query(0,ge=0),limit:int=Query(25,ge=1,le=100),u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    if status and status not in ('requested','quoted','accepted','rejected','in_progress','ready_for_retest','closed'):raise HTTPException(422,'Unknown remediation status.')
    conditions=[Remediation.org_id==org_id,Finding.org_id==org_id]
    if status:conditions.append(Remediation.status==status)
    total=db.scalar(select(func.count()).select_from(Remediation).join(Finding,Finding.id==Remediation.finding_id).where(*conditions))
    rows=db.execute(select(Remediation,Finding).join(Finding,Finding.id==Remediation.finding_id).where(*conditions).order_by(Remediation.created.desc(),Remediation.id).offset(offset).limit(limit))
    from .main import remediation_dict
    return {'total':total,'offset':offset,'limit':limit,'items':[{**remediation_dict(r),'asset_id':f.asset_id,'finding_title':f.title} for r,f in rows]}
