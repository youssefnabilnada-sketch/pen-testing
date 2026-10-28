import os
import time
import secrets
import pyotp
from cryptography.fernet import Fernet,InvalidToken
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import select,update,delete
from .db import database
from .auth import current,digest,hasher,audit
from .models import MfaState,RecoveryCode,LoginSession,User
router=APIRouter(prefix='/auth/mfa',tags=['Authenticator security'])
def cipher():
    try:return Fernet(os.environ['MFA_ENCRYPTION_KEY'].encode())
    except (KeyError,ValueError):raise HTTPException(503,'Authenticator encryption key is not configured on the server.')
def seed(state):
    try:return cipher().decrypt(state.secret.encode()).decode()
    except InvalidToken:raise HTTPException(503,'Authenticator key could not decrypt this account. Contact the operator.')
def counter(secret,code):
    if len(code)!=6 or not code.isascii() or not code.isdigit():return None
    now=int(time.time()//30);otp=pyotp.TOTP(secret)
    for tick in (now-1,now,now+1):
        if secrets.compare_digest(otp.at(tick*30),code):return tick
    return None
def enforce(db,u,code):
    state=db.get(MfaState,u.id)
    if not state or not state.enabled:return
    from .main import throttle
    throttle('mfa:'+u.id)
    if not code:raise HTTPException(401,'Authenticator or recovery code required.')
    normalized=code.strip()
    if len(normalized)==32:
        claimed=db.execute(update(RecoveryCode).where(RecoveryCode.user_id==u.id,RecoveryCode.digest==digest(normalized),RecoveryCode.used.is_(False)).values(used=True))
        if claimed.rowcount:
            audit(db,u,'mfa.recovery_used',u.id);return
    tick=counter(seed(state),normalized)
    if tick is not None:
        claimed=db.execute(update(MfaState).where(MfaState.user_id==u.id,MfaState.enabled.is_(True),MfaState.last_counter<tick).values(last_counter=tick))
        if claimed.rowcount:return
    raise HTTPException(401,'Invalid or already used authenticator/recovery code. Wait for the next code if needed.')
class Password(BaseModel):
    current_password:str=Field(min_length=12,max_length=128)
class Confirm(BaseModel):
    code:str=Field(min_length=6,max_length=64)
class Disable(Password,Confirm):pass
def reauthenticate(u,password):
    from .main import throttle
    throttle('mfa-settings:'+u.id)
    try:hasher.verify(u.password,password)
    except Exception:raise HTTPException(401,'Reauthentication failed.')
@router.get('')
def status(u=Depends(current),db=Depends(database)):
    state=db.get(MfaState,u.id)
    configured=True
    try:cipher()
    except HTTPException:configured=False
    return {'enabled':bool(state and state.enabled),'setup_available':configured}
@router.post('/setup')
def setup(data:Password,request:Request,u=Depends(current),db=Depends(database)):
    reauthenticate(u,data.current_password)
    if not u.verified:raise HTTPException(403,'Verify your email first.')
    db.scalar(select(User).where(User.id==u.id).with_for_update())
    state=db.get(MfaState,u.id)
    if state and state.enabled:raise HTTPException(409,'Authenticator already enabled.')
    secret=pyotp.random_base32();encrypted=cipher().encrypt(secret.encode()).decode()
    if not state:state=MfaState(user_id=u.id);db.add(state)
    state.secret=encrypted;state.enabled=False;state.expires=time.time()+600
    state.enrollment_session=digest(request.cookies['aegis_session']);state.last_counter=-1
    audit(db,u,'mfa.enrollment_started',u.id);db.commit()
    return {'secret':secret,'expires':state.expires,'issuer':'AEGIS','account':u.email}
@router.post('/confirm')
def confirm(data:Confirm,request:Request,u=Depends(current),db=Depends(database)):
    from .main import throttle
    throttle('mfa-settings:'+u.id)
    state=db.scalar(select(MfaState).where(MfaState.user_id==u.id).with_for_update())
    session=digest(request.cookies['aegis_session'])
    if not state or state.enabled or state.expires<=time.time() or state.enrollment_session!=session:
        raise HTTPException(409,'Start a fresh enrollment from this signed-in session.')
    tick=counter(seed(state),data.code)
    if tick is None:raise HTTPException(401,'Invalid authenticator code.')
    claimed=db.execute(update(MfaState).where(MfaState.user_id==u.id,MfaState.enabled.is_(False),MfaState.secret==state.secret,MfaState.expires>time.time()).values(enabled=True,last_counter=tick))
    if not claimed.rowcount:raise HTTPException(409,'Enrollment changed. Start again.')
    codes=[secrets.token_hex(16) for _ in range(10)]
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id==u.id))
    for code in codes:db.add(RecoveryCode(user_id=u.id,digest=digest(code)))
    db.execute(delete(LoginSession).where(LoginSession.user_id==u.id,LoginSession.token_hash!=session))
    audit(db,u,'mfa.enabled',u.id);db.commit()
    return {'recovery_codes':codes,'message':'Authenticator enabled. Other sessions were revoked. Save these recovery codes now; they will not be shown again.'}
@router.post('/disable')
def disable(data:Disable,u=Depends(current),db=Depends(database)):
    reauthenticate(u,data.current_password)
    state=db.get(MfaState,u.id)
    if not state or not state.enabled:raise HTTPException(409,'Authenticator is not enabled.')
    enforce(db,u,data.code)
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id==u.id))
    db.execute(delete(MfaState).where(MfaState.user_id==u.id))
    db.execute(delete(LoginSession).where(LoginSession.user_id==u.id))
    audit(db,u,'mfa.disabled',u.id);db.commit()
    return {'message':'Authenticator disabled. Sign in again.'}
