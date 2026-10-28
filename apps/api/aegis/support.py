import time
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field,field_validator
from sqlalchemy import select
from .db import database
from .auth import current,member,admin,audit
from .models import SupportTicket,SupportMessage,Organization
router=APIRouter(tags=['Support'])
WRITERS=['owner','admin','analyst','engineer']
class MessageInput(BaseModel):
    body:str=Field(min_length=1,max_length=8000)
    @field_validator('body')
    @classmethod
    def nonempty(cls,v):
        if not v.strip():raise ValueError('Message must not be blank.')
        return v.strip()
class TicketInput(MessageInput):
    subject:str=Field(min_length=3,max_length=160)
    @field_validator('subject')
    @classmethod
    def subject_nonempty(cls,v):
        if len(v.strip())<3:raise ValueError('Subject must contain at least three characters.')
        return v.strip()
class StaffInput(MessageInput):
    internal:bool=False
class StatusInput(BaseModel):
    status:str
def ticket(db,u,tid,staff=False,write=False):
    if staff:admin(u)
    t=db.scalar(select(SupportTicket).where(SupportTicket.id==tid).with_for_update()) if write else db.get(SupportTicket,tid)
    if not t:raise HTTPException(404,'Ticket not found.')
    if not staff:member(db,u,t.org_id,roles=WRITERS if write else None)
    return t
def record(t):
    return {'id':t.id,'org_id':t.org_id,'subject':t.subject,'status':t.status,'created':t.created,'updated':t.updated}
def history(db,t,staff,offset):
    q=select(SupportMessage).where(SupportMessage.ticket_id==t.id)
    if not staff:q=q.where(SupportMessage.internal.is_(False))
    return [{'id':m.id,'body':m.body,'internal':m.internal,'staff':m.staff,'created':m.created} for m in db.scalars(q.order_by(SupportMessage.created,SupportMessage.id).offset(offset).limit(100))]
@router.post('/organizations/{org_id}/support',status_code=201)
def create(org_id:str,data:TicketInput,u=Depends(current),db=Depends(database)):
    from .main import throttle
    member(db,u,org_id,roles=WRITERS);throttle('support:'+u.id)
    t=SupportTicket(org_id=org_id,user_id=u.id,subject=data.subject);db.add(t);db.flush()
    db.add(SupportMessage(ticket_id=t.id,user_id=u.id,body=data.body));audit(db,u,'support.created',t.id,org_id);db.commit()
    return record(t)
@router.get('/organizations/{org_id}/support')
def listing(org_id:str,offset:int=Query(0,ge=0),u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    return [record(t) for t in db.scalars(select(SupportTicket).where(SupportTicket.org_id==org_id).order_by(SupportTicket.updated.desc(),SupportTicket.id).offset(offset).limit(50))]
@router.get('/support/{tid}')
def detail(tid:str,offset:int=Query(0,ge=0),u=Depends(current),db=Depends(database)):
    t=ticket(db,u,tid);return {**record(t),'messages':history(db,t,False,offset)}
def reply(db,u,t,data,staff=False):
    from .main import throttle
    throttle('support:'+u.id)
    if t.status=='closed':raise HTTPException(409,'Reopen the ticket before replying.')
    internal=bool(staff and data.internal)
    db.add(SupportMessage(ticket_id=t.id,user_id=u.id,body=data.body,internal=internal,staff=staff))
    if not internal:
        t.updated=time.time();t.status='awaiting_customer' if staff else 'open'
    audit(db,u,'support.internal_note' if internal else 'support.reply',t.id,t.org_id);db.commit()
    return {'message':'Note saved.' if internal else 'Reply saved.'}
@router.post('/support/{tid}/messages')
def customer_reply(tid:str,data:MessageInput,u=Depends(current),db=Depends(database)):
    return reply(db,u,ticket(db,u,tid,write=True),data)
def change(db,u,t,status):
    if status not in ('closed','open'):raise HTTPException(422,'Choose open or closed.')
    if (status=='open' and t.status!='closed') or status==t.status:raise HTTPException(409,'Invalid ticket transition.')
    t.status=status;t.updated=time.time();audit(db,u,'support.'+status,t.id,t.org_id);db.commit();return record(t)
@router.patch('/support/{tid}')
def customer_status(tid:str,data:StatusInput,u=Depends(current),db=Depends(database)):
    return change(db,u,ticket(db,u,tid,write=True),data.status)
@router.get('/admin/support')
def staff_list(offset:int=Query(0,ge=0),u=Depends(current),db=Depends(database)):
    admin(u)
    return [{**record(t),'organization':db.get(Organization,t.org_id).name} for t in db.scalars(select(SupportTicket).order_by(SupportTicket.updated.desc(),SupportTicket.id).offset(offset).limit(50))]
@router.get('/admin/support/{tid}')
def staff_detail(tid:str,offset:int=Query(0,ge=0),u=Depends(current),db=Depends(database)):
    t=ticket(db,u,tid,staff=True);return {**record(t),'messages':history(db,t,True,offset)}
@router.post('/admin/support/{tid}/messages')
def staff_reply(tid:str,data:StaffInput,u=Depends(current),db=Depends(database)):
    return reply(db,u,ticket(db,u,tid,staff=True,write=True),data,True)
@router.patch('/admin/support/{tid}')
def staff_status(tid:str,data:StatusInput,u=Depends(current),db=Depends(database)):
    return change(db,u,ticket(db,u,tid,staff=True,write=True),data.status)
