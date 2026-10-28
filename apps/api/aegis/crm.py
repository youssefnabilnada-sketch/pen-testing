"""Requested demos/beta onboarding; no automatic external outreach or scan permission."""
import time,secrets
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select,func,update
from .auth import current,member,admin,audit,digest
from .db import database
from .models import Lead,User
router=APIRouter(tags=['CRM'])
class Request(BaseModel):
    kind:Literal['demo','beta']
    message:str=Field(min_length=10,max_length=2000)
    contact_consent:bool=False
class Update(BaseModel):
    status:Literal['new','contacted','demo_scheduled','converted','closed']
    note:str=Field(min_length=1,max_length=2000)
    followup_at:float|None=Field(default=None,ge=0)
class Claim(BaseModel):token:str=Field(min_length=20,max_length=100)

@router.post('/organizations/{org_id}/crm-requests')
def request(org_id:str,data:Request,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    from .main import throttle
    throttle('crm:'+u.id)
    if db.scalar(select(func.count()).select_from(Lead).where(Lead.user_id==u.id,Lead.status.not_in(['closed','converted'])))>=5:raise HTTPException(409,'Close an existing request before creating another.')
    row=Lead(org_id=org_id,user_id=u.id,kind=data.kind,message=data.message,contact_consent=data.contact_consent,history=[])
    db.add(row);db.flush();audit(db,u,'crm.requested',row.id,org_id);db.commit();return {'id':row.id,'status':row.status}

@router.get('/organizations/{org_id}/crm-requests')
def own(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    return [{'id':r.id,'kind':r.kind,'status':r.status,'created':r.created,'contact_consent':r.contact_consent} for r in db.scalars(select(Lead).where(Lead.org_id==org_id,Lead.user_id==u.id).order_by(Lead.created.desc()).limit(100))]

@router.post('/organizations/{org_id}/crm-requests/{lead_id}/withdraw-consent')
def withdraw(org_id:str,lead_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    row=db.scalar(select(Lead).where(Lead.id==lead_id,Lead.org_id==org_id,Lead.user_id==u.id).with_for_update())
    if not row:raise HTTPException(404,'Request not found.')
    if row.contact_consent:
        row.contact_consent=False;row.followup_at=None
        row.history=(row.history+[{'at':time.time(),'actor':u.id,'status':row.status,'note':'Customer withdrew contact consent.'}])[-100:]
        audit(db,u,'crm.consent_withdrawn',row.id,org_id)
    db.commit();return {'contact_consent':False,'message_sent':False}

@router.get('/admin/crm')
def dashboard(u=Depends(current),db=Depends(database)):
    admin(u)
    counts=dict(db.execute(select(Lead.status,func.count()).group_by(Lead.status)).all());total=sum(counts.values())
    rows=db.scalars(select(Lead).order_by(Lead.created.desc()).limit(100))
    return {'counts':counts,'conversion_rate':counts.get('converted',0)/total if total else 0,
        'due_followups':db.scalar(select(func.count()).select_from(Lead).where(Lead.contact_consent.is_(True),Lead.followup_at<=time.time(),Lead.status.not_in(['closed','converted']))),
        'items':[{'id':r.id,'org_id':r.org_id,'email':db.get(User,r.user_id).email,'kind':r.kind,'message':r.message,'status':r.status,'contact_consent':r.contact_consent,'followup_at':r.followup_at,'history':r.history} for r in rows]}

@router.patch('/admin/crm/{lead_id}')
def edit(lead_id:str,data:Update,u=Depends(current),db=Depends(database)):
    admin(u);row=db.scalar(select(Lead).where(Lead.id==lead_id).with_for_update())
    if not row:raise HTTPException(404,'Request not found.')
    if data.followup_at is not None and not row.contact_consent:raise HTTPException(409,'Contact consent is required for a follow-up reminder.')
    row.status=data.status;row.followup_at=data.followup_at;row.history=(row.history+[{'at':time.time(),'actor':u.id,'status':data.status,'note':data.note}])[-100:]
    audit(db,u,'crm.updated',row.id,row.org_id);db.commit();return {'saved':True,'message_sent':False}

@router.post('/admin/crm/{lead_id}/beta-invitation')
def invite(lead_id:str,u=Depends(current),db=Depends(database)):
    admin(u);row=db.scalar(select(Lead).where(Lead.id==lead_id).with_for_update())
    if not row or row.kind!='beta':raise HTTPException(404,'Beta request not found.')
    if row.status in ('closed','converted'):raise HTTPException(409,'Request is no longer open.')
    token=secrets.token_urlsafe(32);row.invite_digest=digest(token);row.invite_expires=time.time()+86400;row.status='beta_invited'
    row.history=(row.history+[{'at':time.time(),'actor':u.id,'status':'beta_invited','note':'Single-use invitation prepared; no message sent.'}])[-100:]
    audit(db,u,'crm.beta_invited',row.id,row.org_id);db.commit()
    return {'token':token,'expires':row.invite_expires,'message_sent':False,'instruction':'Share only through an explicitly approved communication channel.'}

@router.post('/crm/beta-accept')
def accept(data:Claim,u=Depends(current),db=Depends(database)):
    row=db.scalar(select(Lead).where(Lead.user_id==u.id,Lead.invite_digest==digest(data.token),Lead.invite_expires>time.time(),Lead.status=='beta_invited').with_for_update())
    if not row:raise HTTPException(400,'Invalid, expired or consumed invitation.')
    member(db,u,row.org_id);row.invite_digest=None;row.invite_expires=None;row.status='converted'
    row.history=(row.history+[{'at':time.time(),'actor':u.id,'status':'converted','note':'Customer accepted private beta invitation.'}])[-100:]
    audit(db,u,'crm.beta_accepted',row.id,row.org_id);db.commit();return {'accepted':True,'assessment_authorized':False}
