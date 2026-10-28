import os
import re
import time
from email.message import EmailMessage
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import database
from .auth import current, member, audit, smtp_connection
from .models import TeamInvitation, Organization, Membership, User

router=APIRouter(tags=['Team invitations'])
ROLES=('admin','analyst','engineer','viewer')

class InviteInput(BaseModel):
    email:str=Field(min_length=5,max_length=254)
    role:str

class RoleInput(BaseModel):
    role:str

def manage(db,u,org,role=None,target=None):
    actor=member(db,u,org,roles=['owner','admin'])
    if role is not None and role not in ROLES:raise HTTPException(422,'Invalid role.')
    if target and target.role=='owner':raise HTTPException(403,'Owner membership cannot be changed here.')
    if actor.role!='owner' and (role=='admin' or (target and target.role=='admin')):
        raise HTTPException(403,'Only the owner may manage administrator membership.')
    return actor

def send_invitation(email,organization):
    message=EmailMessage()
    message['From']=os.getenv('MAIL_FROM','security@aegis.local')
    message['To']=email;message['Subject']='AEGIS workspace invitation'
    message.set_content(f'You were invited to {organization}. Sign in or register using this email address, verify it, and review Incoming workspace invitations. No access is granted until you accept. The invitation expires in 48 hours.\n{os.getenv("WEB_ORIGIN","http://localhost:3000")}/console')
    with smtp_connection() as smtp:smtp.send_message(message)

def serialized(invite):
    return {'id':invite.id,'email':invite.email,'role':invite.role,'expires':invite.expires,
            'status':'expired' if invite.status=='pending' and invite.expires<=time.time() else invite.status}

@router.post('/organizations/{org_id}/invitations',status_code=201)
def invite(org_id:str,data:InviteInput,u=Depends(current),db=Depends(database)):
    from .main import throttle
    manage(db,u,org_id,data.role);throttle('invite:'+u.id)
    email=data.email.strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise HTTPException(422,'Valid email required.')
    org=db.scalar(select(Organization).where(Organization.id==org_id).with_for_update())
    existing_user=db.scalar(select(User).where(User.email==email))
    if existing_user and db.scalar(select(Membership).where(Membership.org_id==org_id,Membership.user_id==existing_user.id)):
        raise HTTPException(409,'Already a workspace member.')
    if db.scalar(select(TeamInvitation).where(TeamInvitation.org_id==org_id,TeamInvitation.email==email,TeamInvitation.status=='pending',TeamInvitation.expires>time.time())):
        raise HTTPException(409,'An active invitation already exists.')
    item=TeamInvitation(org_id=org_id,email=email,role=data.role,invited_by=u.id,expires=time.time()+172800)
    db.add(item);db.flush()
    try:send_invitation(email,org.name)
    except Exception:
        db.rollback();raise HTTPException(503,'Invitation email could not be sent. No invitation was saved.')
    audit(db,u,'team.invited',item.id,org_id);db.commit()
    return serialized(item)

@router.get('/organizations/{org_id}/invitations')
def invitations(org_id:str,u=Depends(current),db=Depends(database)):
    manage(db,u,org_id)
    return [serialized(i) for i in db.scalars(select(TeamInvitation).where(TeamInvitation.org_id==org_id).order_by(TeamInvitation.created.desc()).limit(100))]

@router.delete('/organizations/{org_id}/invitations/{invitation_id}')
def revoke(org_id:str,invitation_id:str,u=Depends(current),db=Depends(database)):
    manage(db,u,org_id)
    item=db.scalar(select(TeamInvitation).where(TeamInvitation.id==invitation_id,TeamInvitation.org_id==org_id).with_for_update())
    if not item:raise HTTPException(404,'Invitation not found.')
    manage(db,u,org_id,item.role)
    if item.status!='pending':raise HTTPException(409,'Invitation is no longer pending.')
    item.status='revoked';audit(db,u,'team.invitation_revoked',item.id,org_id);db.commit()
    return {'message':'Invitation revoked.'}

@router.get('/invitations/incoming')
def incoming(u=Depends(current),db=Depends(database)):
    if not u.verified:raise HTTPException(403,'Verify your email before reviewing invitations.')
    return [{**serialized(i),'organization':db.get(Organization,i.org_id).name} for i in db.scalars(select(TeamInvitation).where(TeamInvitation.email==u.email,TeamInvitation.status=='pending',TeamInvitation.expires>time.time()).limit(100))]

@router.post('/invitations/{invitation_id}/accept')
def accept(invitation_id:str,u=Depends(current),db=Depends(database)):
    if not u.verified:raise HTTPException(403,'Verify your email before accepting.')
    item=db.scalar(select(TeamInvitation).where(TeamInvitation.id==invitation_id,TeamInvitation.email==u.email).with_for_update())
    if not item:raise HTTPException(404,'Invitation not found for this account.')
    if item.status!='pending' or item.expires<=time.time():raise HTTPException(409,'Invitation expired or no longer pending.')
    # Recheck inviter authority: a removed/demoted inviter cannot grant stale privileges.
    inviter=db.get(User,item.invited_by)
    if not inviter or not inviter.active:raise HTTPException(409,'Inviter is no longer active. Request a new invitation.')
    manage(db,inviter,item.org_id,item.role)
    db.add(Membership(org_id=item.org_id,user_id=u.id,role=item.role))
    item.status='accepted';item.accepted_by=u.id;audit(db,u,'team.invitation_accepted',item.id,item.org_id)
    try:db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Membership already exists.')
    return {'org_id':item.org_id,'message':'Invitation accepted.'}

@router.patch('/organizations/{org_id}/members/{user_id}')
def change_role(org_id:str,user_id:str,data:RoleInput,u=Depends(current),db=Depends(database)):
    manage(db,u,org_id,data.role)
    target=db.scalar(select(Membership).where(Membership.org_id==org_id,Membership.user_id==user_id).with_for_update())
    if not target:raise HTTPException(404,'Member not found.')
    manage(db,u,org_id,data.role,target)
    target.role=data.role;audit(db,u,'team.role_changed',user_id,org_id);db.commit()
    return {'message':'Role updated.'}

@router.delete('/organizations/{org_id}/members/{user_id}')
def remove(org_id:str,user_id:str,u=Depends(current),db=Depends(database)):
    manage(db,u,org_id)
    target=db.scalar(select(Membership).where(Membership.org_id==org_id,Membership.user_id==user_id).with_for_update())
    if not target:raise HTTPException(404,'Member not found.')
    manage(db,u,org_id,target=target)
    db.delete(target);audit(db,u,'team.removed',user_id,org_id);db.commit()
    return {'message':'Workspace membership removed.'}
