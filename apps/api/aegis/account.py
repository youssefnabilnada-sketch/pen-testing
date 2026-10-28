from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel,Field,ConfigDict,field_validator
from sqlalchemy import select,delete
from .auth import current,hasher,audit
from .db import database
from .models import User,Membership,LoginSession,EmailToken
from .mfa import reauthenticate,enforce
router=APIRouter(prefix='/auth/account',tags=['Account lifecycle'])
class Profile(BaseModel):
    model_config=ConfigDict(extra='forbid')
    display_name:str=Field(min_length=1,max_length=100)
    @field_validator('display_name')
    @classmethod
    def valid_name(cls,value):
        if not value.strip() or any(ord(c)<32 for c in value):raise ValueError('Use a nonempty display name without control characters.')
        return value.strip()
class Confirm(BaseModel):
    model_config=ConfigDict(extra='forbid')
    current_password:str=Field(min_length=12,max_length=128)
    mfa_code:str=Field(default='',max_length=64)
class PasswordChange(Confirm):
    new_password:str=Field(min_length=12,max_length=128)
class Deactivate(Confirm):
    confirm_deactivation:bool
def verify(db,u,data):
    # Serialize lifecycle changes for one account before evaluating current credentials.
    locked=db.scalar(select(User).where(User.id==u.id).with_for_update().execution_options(populate_existing=True))
    if not locked.active:raise HTTPException(401,'Account unavailable.')
    reauthenticate(locked,data.current_password);enforce(db,locked,data.mfa_code)
    return locked
def revoke(db,u,response):
    db.execute(delete(LoginSession).where(LoginSession.user_id==u.id))
    db.execute(delete(EmailToken).where(EmailToken.user_id==u.id))
    response.delete_cookie('aegis_session',path='/')
@router.get('')
def profile(u=Depends(current)):
    return {'display_name':u.display_name,'email':u.email,'verified':u.verified}
@router.patch('')
def update_profile(data:Profile,u=Depends(current),db=Depends(database)):
    u.display_name=data.display_name;audit(db,u,'account.profile_changed',u.id);db.commit()
    return {'display_name':u.display_name}
@router.post('/password')
def change_password(data:PasswordChange,response:Response,u=Depends(current),db=Depends(database)):
    u=verify(db,u,data)
    if data.new_password==data.current_password:raise HTTPException(422,'Choose a different password.')
    u.password=hasher.hash(data.new_password);revoke(db,u,response)
    audit(db,u,'account.password_changed',u.id);db.commit()
    return {'message':'Password changed. All sessions and pending account email tokens were revoked.'}
@router.post('/sign-out-all')
def sign_out_all(data:Confirm,response:Response,u=Depends(current),db=Depends(database)):
    u=verify(db,u,data);revoke(db,u,response);audit(db,u,'account.sessions_revoked',u.id);db.commit()
    return {'message':'All sessions and pending account email tokens were revoked.'}
@router.post('/deactivate')
def deactivate(data:Deactivate,response:Response,u=Depends(current),db=Depends(database)):
    if not data.confirm_deactivation:raise HTTPException(422,'Explicit account deactivation confirmation is required.')
    u=verify(db,u,data)
    if u.superadmin:raise HTTPException(409,'Platform administrator deactivation requires a separate administrative review.')
    if db.scalar(select(Membership.id).where(Membership.user_id==u.id,Membership.role=='owner')):
        raise HTTPException(409,'An organization owner cannot deactivate. Ownership must first be transferred through an authorized ownership process.')
    u.active=False;revoke(db,u,response);audit(db,u,'account.deactivated',u.id);db.commit()
    return {'message':'Account deactivated. Workspace evidence and audit records are retained; this is not a data-erasure request.'}
