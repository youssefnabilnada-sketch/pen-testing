"""Optional identity adapter. Never grants asset ownership or deploy access."""
import os
import secrets
import time
import re
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import database
from .models import FirebaseIdentity, User, LoginSession
from .auth import current, hasher, digest, audit
router = APIRouter(prefix='/auth/firebase', tags=['Optional Firebase identity'])

def emulator_enabled():
    host = os.getenv('FIREBASE_AUTH_EMULATOR_HOST', '')
    if not host:
        return False
    from urllib.parse import urlsplit
    origin = urlsplit(os.getenv('WEB_ORIGIN', 'http://localhost:3000'))
    if (os.getenv('AEGIS_ENV') not in ('development', 'test')
        or os.getenv('AEGIS_FIREBASE_EMULATOR') != 'true'
        or os.getenv('FIREBASE_PROJECT_ID') != 'demo-aegis'
        or host not in ('127.0.0.1:9099', 'localhost:9099', 'firebase-emulator:9099')
        or origin.hostname not in ('localhost', '127.0.0.1')):
        raise HTTPException(503, 'Firebase emulator requires explicit local-only demo configuration.')
    return True

def project_id():
    value = os.getenv('FIREBASE_PROJECT_ID','')
    if os.getenv('FIREBASE_AUTH_ENABLED','false') != 'true' or not value:
        raise HTTPException(503, 'Firebase identity integration is not configured.')
    emulator_enabled()
    return value

def firebase_app(project):
    import firebase_admin
    try:
        app = firebase_admin.get_app('aegis-identity')
    except ValueError:
        app = firebase_admin.initialize_app(options={'projectId':project,'httpTimeout':5}, name='aegis-identity')
    if app.project_id != project:
        raise HTTPException(503,'Firebase server project configuration changed. Restart the API.')
    # Accessing the credential validates ADC before we classify token errors.
    if emulator_enabled():
        return app
    credential=app.credential.get_credential()
    credential_project=getattr(credential,'project_id',None)
    if credential_project and credential_project != project:
        raise HTTPException(503,'Firebase server credential belongs to a different project.')
    return app

def sdk_verify(token, project):
    try:
        from firebase_admin import auth
        from google.auth.exceptions import DefaultCredentialsError
        app = firebase_app(project)
        return auth.verify_id_token(token, app=app, check_revoked=True)
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(503, 'Install the optional Firebase identity dependencies.')
    except DefaultCredentialsError:
        raise HTTPException(503, 'Firebase server credentials are unavailable. Run the local connection setup.')
    except Exception:
        raise HTTPException(401, 'Firebase identity could not be verified. Sign in again.')

def verified_identity(token):
    project = project_id()
    claims = sdk_verify(token, project)
    now = time.time()
    auth_time = claims.get('auth_time',0)
    if (claims.get('aud') != project or claims.get('iss') != 'https://securetoken.google.com/'+project
        or claims.get('email_verified') is not True or not isinstance(claims.get('sub'),str)
        or not 1 <= len(claims['sub']) <= 128 or not isinstance(auth_time,(int,float))
        or not 0 <= now-auth_time <= 300):
        raise HTTPException(401, 'Use a verified Firebase account and sign in again within five minutes.')
    return project, claims

class IdentityInput(BaseModel):
    id_token: str = Field(min_length=20,max_length=16000)
    mfa_code: str = Field(default='',max_length=64)

class PasswordInput(BaseModel):
    mfa_code: str = Field(default='',max_length=64)
    current_password: str = Field(min_length=12,max_length=128)

class LinkInput(IdentityInput, PasswordInput):
    pass

class RegisterInput(IdentityInput):
    recovery_password: str = Field(min_length=12,max_length=128)

@router.post('/link')
def link(data: LinkInput, request: Request, u=Depends(current), db=Depends(database)):
    from .main import throttle
    throttle('firebase-link:'+u.id)
    if not u.verified:
        raise HTTPException(403,'Verify your AEGIS account first.')
    try:
        hasher.verify(u.password,data.current_password)
    except Exception:
        raise HTTPException(401,'Reauthentication failed.')
    from .mfa import enforce
    enforce(db,u,data.mfa_code)
    project, claims = verified_identity(data.id_token)
    subject = claims['sub']
    db.add(FirebaseIdentity(user_id=u.id,project=project,subject=subject))
    audit(db,u,'identity.firebase.linked',u.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,'Identity is already linked. Unlink before changing it.')
    return {'message':'Firebase identity linked. Workspace and asset permissions are unchanged.'}

@router.post('/login')
def login(data: IdentityInput, request: Request, response: Response, db=Depends(database)):
    from .main import throttle
    throttle('firebase-login:'+request.client.host)
    project, claims = verified_identity(data.id_token)
    subject = claims['sub']
    identity = db.scalar(select(FirebaseIdentity).where(FirebaseIdentity.project==project,FirebaseIdentity.subject==subject))
    u = db.get(User,identity.user_id) if identity else None
    if not u or not u.active or not u.verified:
        raise HTTPException(401,'No active linked AEGIS account. Sign in locally and link your identity first.')
    from .mfa import enforce
    enforce(db,u,data.mfa_code)
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    # Short session bounds upstream revocation delay; no Firebase token persisted.
    db.add(LoginSession(user_id=u.id,token_hash=digest(token),csrf=csrf,expires=time.time()+900))
    audit(db,u,'identity.firebase.login',u.id)
    db.commit()
    response.set_cookie('aegis_session',token,httponly=True,secure=os.getenv('COOKIE_SECURE','true')=='true',samesite='strict',max_age=900,path='/')
    return {'csrf':csrf}

@router.delete('/link')
def unlink(data: PasswordInput, u=Depends(current), db=Depends(database)):
    from .main import throttle
    throttle('firebase-unlink:'+u.id)
    try:
        hasher.verify(u.password,data.current_password)
    except Exception:
        raise HTTPException(401,'Reauthentication failed.')
    from .mfa import enforce
    enforce(db,u,data.mfa_code)
    identity=db.scalar(select(FirebaseIdentity).where(FirebaseIdentity.user_id==u.id))
    if identity:
        db.delete(identity)
    for session in db.scalars(select(LoginSession).where(LoginSession.user_id==u.id)):
        db.delete(session)
    audit(db,u,'identity.firebase.unlinked',u.id)
    db.commit()
    return {'message':'Identity unlinked and all local sessions revoked.'}


@router.get('/config')
def config():
    """Only public web configuration. No credentials or service-account information."""
    project = os.getenv('FIREBASE_PROJECT_ID', '')
    key = os.getenv('FIREBASE_WEB_API_KEY', '')
    app_id = os.getenv('FIREBASE_WEB_APP_ID', '')
    try:
        emulator = emulator_enabled()
    except HTTPException:
        return {'enabled': False}
    enabled = os.getenv('FIREBASE_AUTH_ENABLED') == 'true' and bool(project and key and app_id)
    if not enabled:
        return {'enabled': False}
    config = {'projectId': project, 'apiKey': key, 'appId': app_id, 'authDomain': project+'.firebaseapp.com'}
    if emulator: config['emulatorUrl'] = 'http://127.0.0.1:9099'
    return {'enabled': True, 'config': config}

@router.get('/status')
def status(u=Depends(current), db=Depends(database)):
    identity = db.scalar(select(FirebaseIdentity).where(FirebaseIdentity.user_id==u.id))
    return {'linked': bool(identity), 'project': identity.project if identity else None}

@router.post('/register', status_code=201)
def register(data: RegisterInput, request: Request, udb=Depends(database)):
    from .main import throttle
    throttle('firebase-register:'+request.client.host)
    project, claims = verified_identity(data.id_token)
    email = claims.get('email', '')
    if not isinstance(email,str) or len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
        raise HTTPException(422,'A verified email address is required.')
    email=email.strip().lower()
    if udb.scalar(select(User).where(User.email==email)):
        raise HTTPException(409,'An AEGIS account already exists. Sign in locally and link it from Account security.')
    u=User(email=email,password=hasher.hash(data.recovery_password),verified=True)
    udb.add(u)
    try:
        udb.flush()
        udb.add(FirebaseIdentity(user_id=u.id,project=project,subject=claims['sub']))
        audit(udb,u,'identity.firebase.registered',u.id)
        udb.commit()
    except IntegrityError:
        udb.rollback()
        raise HTTPException(409,'Account or identity already exists. Use sign in or explicit linking.')
    return {'message':'AEGIS account created. Sign in to create your workspace.'}
