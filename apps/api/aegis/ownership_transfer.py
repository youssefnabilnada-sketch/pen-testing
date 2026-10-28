from fastapi import APIRouter,Depends,HTTPException
from pydantic import Field
from sqlalchemy import select
from .db import database
from .auth import current,member,audit
from .account import Confirm,verify
from .models import User,Organization,Membership
router=APIRouter(tags=['Organization ownership'])
class Transfer(Confirm):
    target_user_id:str=Field(min_length=36,max_length=36)
    confirm_email:str=Field(min_length=5,max_length=254)
    confirm_transfer:bool
@router.post('/organizations/{org}/transfer-ownership')
def transfer(org:str,data:Transfer,u=Depends(current),db=Depends(database)):
    if not data.confirm_transfer:raise HTTPException(422,'Explicit ownership transfer confirmation is required.')
    if data.target_user_id==u.id:raise HTTPException(422,'Choose a different administrator.')
    member(db,u,org,roles=['owner'])
    # Consistent account lock order serializes deactivation and concurrent transfers.
    db.scalars(select(User).where(User.id.in_([u.id,data.target_user_id])).order_by(User.id).with_for_update().execution_options(populate_existing=True)).all()
    db.scalar(select(Organization).where(Organization.id==org).with_for_update())
    owner=db.scalar(select(Membership).where(Membership.org_id==org,Membership.user_id==u.id).with_for_update().execution_options(populate_existing=True))
    target=db.scalar(select(Membership).where(Membership.org_id==org,Membership.user_id==data.target_user_id).with_for_update().execution_options(populate_existing=True))
    if not owner or owner.role!='owner':raise HTTPException(403,'Current owner permission required.')
    recipient=db.get(User,data.target_user_id)
    if not target or target.role!='admin' or not recipient or not recipient.active or not recipient.verified:
        raise HTTPException(409,'Choose an active verified administrator already in this workspace.')
    if data.confirm_email.strip().lower()!=recipient.email:raise HTTPException(422,'Confirmation email does not match the selected administrator.')
    verify(db,u,data)
    owner.role='admin';target.role='owner'
    audit(db,u,'organization.ownership_transferred',recipient.id,org);db.commit()
    return {'message':'Ownership transferred. Your membership is now administrator.','owner_user_id':recipient.id}
