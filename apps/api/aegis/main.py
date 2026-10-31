import os
from typing import Literal
import re
import secrets
import time
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from .db import database
from .historical_records import asset_origin
from .models import User, LoginSession, EmailToken, Organization, Membership, Asset, Challenge, Authorization, Job, Finding, FindingHistory, Report, Remediation, Message, Audit, Setting
from .auth import current, member, admin, audit, digest, hasher, send_token
from .runtime import validate_runtime
from .request_origins import allowed_request_origins

validate_runtime('api')

app = FastAPI(title='AEGIS Security Cloud', version='0.1.0', description='Authorized configuration assessment. Not comprehensive penetration testing. Payments disabled.')

@app.middleware('http')
async def security_headers(request: Request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin and origin not in allowed_request_origins():
            return Response(status_code=403, content='Untrusted origin')
    result = await call_next(request)
    result.headers['X-Content-Type-Options'] = 'nosniff'
    result.headers['Cache-Control'] = 'no-store'
    result.headers['X-Frame-Options'] = 'DENY'
    return result

class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    mfa_code: str = Field(default='',max_length=64)

class EmailInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)

class TokenInput(BaseModel):
    token: str = Field(min_length=20, max_length=150)

class ResetInput(TokenInput):
    password: str = Field(min_length=12, max_length=128)

class OrgInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)

def throttle(key, limit=12):
    if os.getenv('TESTING') == '1':
        return
    import redis
    from redis.exceptions import RedisError
    try:
        r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        # Atomic counter/expiry; fixed window, fail closed when coordination is unavailable.
        n = r.eval("local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n", 1, 'rate:'+key)
        if n > limit:
            raise HTTPException(429, 'Too many attempts. Try again in one minute.')
    except RedisError:
        raise HTTPException(503, 'Authentication coordination unavailable.')

def throttle_public_account(request, action, email):
    """Bound credential stuffing without treating shared reverse-proxy IPs as a single user.

    The source cap guards abusive high-cardinality attempts; the hashed account
    key provides a much tighter per-identity cap. Untrusted X-Forwarded-For is
    deliberately ignored rather than granting clients control of rate keys.
    """
    normalized = email.strip().lower()
    identity = digest(normalized)
    throttle('public:'+action+':source:'+request.client.host, limit=240)
    throttle('public:'+action+':identity:'+identity)


def email_token(db, user, purpose):
    token = secrets.token_urlsafe(32)
    db.execute(delete(EmailToken).where(EmailToken.user_id == user.id, EmailToken.purpose == purpose))
    db.add(EmailToken(user_id=user.id, digest=digest(token), purpose=purpose, expires=time.time()+1800))
    try:
        send_token(user.email, token, purpose)
    except OSError:
        raise HTTPException(503, 'Email service unavailable. Please retry.')

@app.get('/health')
def health(db=Depends(database)):
    db.execute(select(1))
    return {'database': 'reachable', 'payments_enabled': False, 'billing_mode': 'disabled', 'coverage': 'root response configuration only'}

@app.get('/ready')
def ready(response:Response):
    from .connections import readiness
    state=readiness()
    response.status_code=200 if state['ready'] else 503
    return state

@app.get('/admin/connections')
def connections(u=Depends(current)):
    admin(u)
    from .connections import diagnose
    return diagnose()

@app.post('/auth/register', status_code=201)
def register(data: Credentials, request: Request, db=Depends(database)):
    email = data.email.strip().lower()
    throttle_public_account(request, 'register', email)
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise HTTPException(422, 'Enter a valid email address.')
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, 'Account cannot be created. Try sign in or password reset.')
    u = User(email=email, password=hasher.hash(data.password))
    db.add(u)
    db.flush()
    email_token(db, u, 'verify')
    audit(db, u, 'account.registered', u.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Account already exists.')
    return {'message': 'Check your email for a verification token.'}

@app.post('/auth/verify')
def verify_email(data: TokenInput, db=Depends(database)):
    t = db.scalar(select(EmailToken).where(EmailToken.digest == digest(data.token), EmailToken.purpose == 'verify').with_for_update())
    if not t or t.expires < time.time():
        raise HTTPException(400, 'Invalid or expired token.')
    db.get(User, t.user_id).verified = True
    db.delete(t)
    db.commit()
    return {'message': 'Email verified. You can sign in.'}

@app.post('/auth/login')
def login(data: Credentials, request: Request, response: Response, db=Depends(database)):
    throttle_public_account(request, 'login', data.email)
    u = db.scalar(select(User).where(User.email == data.email.strip().lower()))
    try:
        hasher.verify(u.password if u else DUMMY_HASH, data.password)
    except Exception:
        raise HTTPException(401, 'Invalid email or password.')
    if not u or not u.active:
        raise HTTPException(401, 'Invalid email or password.')
    from .mfa import enforce
    enforce(db,u,data.mfa_code)
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add(LoginSession(user_id=u.id, token_hash=digest(token), csrf=csrf, expires=time.time()+28800))
    audit(db, u, 'account.login', u.id)
    db.commit()
    response.set_cookie('aegis_session', token, httponly=True, secure=os.getenv('COOKIE_SECURE', 'true') == 'true', samesite='strict', max_age=28800, path='/')
    return {'csrf': csrf}

DUMMY_HASH = hasher.hash(secrets.token_urlsafe(24))

@app.get('/auth/me')
def me(request: Request, u=Depends(current), db=Depends(database)):
    s = db.scalar(select(LoginSession).where(LoginSession.token_hash == digest(request.cookies['aegis_session'])))
    memberships = db.scalars(select(Membership).where(Membership.user_id == u.id)).all()
    return {'id': u.id, 'email': u.email, 'verified': u.verified, 'superadmin': u.superadmin, 'csrf': s.csrf,
            'organizations': [{'id': m.org_id, 'name': db.get(Organization, m.org_id).name, 'role': m.role} for m in memberships]}

@app.post('/auth/logout')
def logout(request: Request, response: Response, u=Depends(current), db=Depends(database)):
    db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(request.cookies['aegis_session'])))
    db.commit()
    response.delete_cookie('aegis_session', path='/')
    return {'message': 'Signed out.'}

@app.post('/auth/reset-request')
def reset_request(data: EmailInput, request: Request, db=Depends(database)):
    throttle_public_account(request, 'reset-request', data.email)
    u = db.scalar(select(User).where(User.email == data.email.strip().lower(), User.active.is_(True)))
    if u:
        email_token(db, u, 'reset')
        db.commit()
    return {'message': 'If the account exists, a reset token has been emailed.'}

@app.post('/auth/reset')
def reset(data: ResetInput, db=Depends(database)):
    t = db.scalar(select(EmailToken).where(EmailToken.digest == digest(data.token), EmailToken.purpose == 'reset').with_for_update())
    if not t or t.expires < time.time():
        raise HTTPException(400, 'Invalid or expired token.')
    u = db.get(User, t.user_id)
    u.password = hasher.hash(data.password)
    db.execute(delete(LoginSession).where(LoginSession.user_id == u.id))
    db.delete(t)
    audit(db, u, 'account.password_reset', u.id)
    db.commit()
    return {'message': 'Password changed. All sessions revoked.'}

@app.post('/auth/deactivate')
def legacy_deactivate(u=Depends(current)):
    raise HTTPException(409, 'Use Account security to confirm your password and review account deactivation.')

@app.post('/organizations', status_code=201)
def create_org(data: OrgInput, u=Depends(current), db=Depends(database)):
    u=db.scalar(select(User).where(User.id==u.id).with_for_update().execution_options(populate_existing=True))
    if not u.active:raise HTTPException(401,'Account unavailable.')
    if not u.verified:
        raise HTTPException(403, 'Verify your email first.')
    org = Organization(name=data.name.strip())
    db.add(org)
    db.flush()
    db.add(Membership(user_id=u.id, org_id=org.id, role='owner'))
    audit(db, u, 'organization.created', org.id, org.id)
    db.commit()
    return {'id': org.id, 'name': org.name}

class MemberInput(BaseModel):
    email: str
    role: str

@app.post('/organizations/{org_id}/members')
def add_member(org_id: str, data: MemberInput, u=Depends(current), db=Depends(database)):
    from .team import manage
    manage(db,u,org_id,data.role)
    if data.role not in ['admin', 'analyst', 'engineer', 'viewer']:
        raise HTTPException(422, 'Invalid role.')
    other = db.scalar(select(User).where(User.email == data.email.lower(), User.verified.is_(True), User.active.is_(True)))
    if not other:
        raise HTTPException(404, 'Use a team invitation for someone without a verified account.')
    existing = db.scalar(select(Membership).where(Membership.org_id == org_id, Membership.user_id == other.id))
    if existing:
        raise HTTPException(409, 'Already a member.')
    db.add(Membership(org_id=org_id, user_id=other.id, role=data.role))
    audit(db, u, 'member.added', other.id, org_id)
    db.commit()
    return {'message': 'Member added.'}

@app.get('/organizations/{org_id}/members')
def members(org_id: str, u=Depends(current), db=Depends(database)):
    member(db, u, org_id)
    return [{'id': m.user_id, 'email': db.get(User, m.user_id).email, 'role': m.role} for m in db.scalars(select(Membership).where(Membership.org_id == org_id))]

class AssetInput(BaseModel):
    origin: str = Field(max_length=300)

class ChallengeInput(BaseModel):
    method: str

class AuthorizationInput(BaseModel):
    accepted: bool
    profile: Literal['web','api'] = 'web'
    paths: list[str] = Field(default_factory=lambda:['/'],min_length=1,max_length=20)
    hours: int = Field(default=24, ge=1, le=24)

def asset_access(db, u, asset_id, write=False):
    a = db.get(Asset, asset_id)
    if not a:
        raise HTTPException(404, 'Asset not found.')
    member(db, u, a.org_id, write=write)
    return a

@app.post('/organizations/{org_id}/assets', status_code=201)
def create_asset(org_id: str, data: AssetInput, u=Depends(current), db=Depends(database)):
    from .safety import canonical_origin, resolve, UnsafeTarget
    member(db, u, org_id, roles=['owner', 'admin', 'analyst'])
    try:
        origin = canonical_origin(data.origin)
        resolve(origin)
    except UnsafeTarget as exc:
        raise HTTPException(422, str(exc))
    a = Asset(org_id=org_id, origin=origin)
    db.add(a)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Asset already registered.')
    audit(db, u, 'asset.created', a.id, org_id)
    db.commit()
    return {'id': a.id, 'origin': origin}

@app.get('/organizations/{org_id}/assets')
def assets(org_id: str, u=Depends(current), db=Depends(database)):
    member(db, u, org_id)
    return [{'id':a.id,'origin':a.origin,'verified':a.verified_until>time.time(),'verified_until':a.verified_until} for a in db.scalars(select(Asset).where(Asset.org_id==org_id).order_by(Asset.created.desc()))]

@app.post('/assets/{asset_id}/challenge')
def challenge(asset_id: str, data: ChallengeInput, u=Depends(current), db=Depends(database)):
    a = asset_access(db, u, asset_id, True)
    if data.method not in ('dns', 'file', 'meta'):
        raise HTTPException(422, 'Use dns, file or meta.')
    from .onboarding import instructions
    c = db.scalar(select(Challenge).where(Challenge.asset_id == a.id,
        Challenge.method == data.method, Challenge.consumed.is_(False),
        Challenge.expires > time.time()).order_by(Challenge.expires.desc()))
    if not c:
        c = Challenge(asset_id=a.id, method=data.method, token=secrets.token_urlsafe(32), expires=time.time()+3600)
        db.add(c)
        audit(db, u, 'ownership.challenge.created', a.id, a.org_id)
        db.commit()
    return instructions(a.origin, c)

@app.get('/assets/{asset_id}/challenge')
def active_challenge(asset_id: str, u=Depends(current), db=Depends(database)):
    from .onboarding import instructions
    a = asset_access(db, u, asset_id, True)
    c = db.scalar(select(Challenge).where(Challenge.asset_id == a.id,
        Challenge.consumed.is_(False), Challenge.expires > time.time()).order_by(Challenge.expires.desc()))
    return instructions(a.origin, c) if c else None

class GitHubHelperInput(BaseModel):
    repository: str = Field(max_length=150)
    branch: str = Field(default='main', max_length=100)
    directory: str = Field(default='', max_length=10)

@app.post('/assets/{asset_id}/challenge/{challenge_id}/github')
def github_helper(asset_id: str, challenge_id: str, data: GitHubHelperInput, u=Depends(current), db=Depends(database)):
    from .onboarding import github_link
    a = asset_access(db, u, asset_id, True)
    c = db.get(Challenge, challenge_id)
    if not c or c.asset_id != a.id or c.method != 'file' or c.consumed or c.expires <= time.time():
        raise HTTPException(400, 'Create a current file verification challenge first.')
    return {'url': github_link(data.repository, data.branch, data.directory, c),
            'message': 'Review and commit on GitHub, wait for deployment, then check ownership. No access to your repository is granted to AEGIS.'}

@app.post('/assets/{asset_id}/verify/{challenge_id}')
def verify_asset(asset_id: str, challenge_id: str, u=Depends(current), db=Depends(database)):
    from .verification import verify
    a = asset_access(db, u, asset_id, True)
    throttle('verification:'+a.id)
    c = db.get(Challenge, challenge_id)
    if not c or c.asset_id != a.id or c.expires < time.time() or c.consumed:
        raise HTTPException(400, 'Invalid, expired or consumed verification challenge.')
    try:
        valid = verify(a.origin, c)
    except Exception:
        raise HTTPException(400, 'Verification could not complete. Check DNS, destination safety and published token.')
    if not valid:
        raise HTTPException(400, 'Ownership token did not match.')
    # Recheck after network I/O; a revoked/expired proof cannot regain ownership.
    db.refresh(c)
    if c.consumed or c.expires<=time.time():
        raise HTTPException(400,'Verification challenge expired or was revoked during verification.')
    from sqlalchemy import update as sql_update
    claim=db.execute(sql_update(Challenge).where(Challenge.id==c.id,Challenge.consumed.is_(False),Challenge.expires>time.time()).values(consumed=True))
    if not claim.rowcount:
        raise HTTPException(409,'Verification challenge was already consumed.')
    a.verified_until = time.time()+86400
    audit(db, u, 'asset.verified', a.id, a.org_id)
    db.commit()
    return {'message':'Ownership verified for this exact origin for 24 hours.'}

@app.post('/assets/{asset_id}/revoke')
def revoke_asset(asset_id: str, u=Depends(current), db=Depends(database)):
    a = asset_access(db, u, asset_id, True)
    a.verified_until = 0
    for c in db.scalars(select(Challenge).where(Challenge.asset_id == asset_id)):
        c.consumed = True
    for auth in db.scalars(select(Authorization).where(Authorization.asset_id==asset_id)):
        auth.revoked = True
    for job in db.scalars(select(Job).where(Job.asset_id==asset_id, Job.status.in_(['queued','preparing','running']))):
        job.cancel = True
    audit(db, u, 'asset.revoked', a.id, a.org_id)
    db.commit()
    return {'message':'Ownership revoked; active jobs will stop at their next checkpoint.'}

@app.post('/assets/{asset_id}/authorize')
def authorize(asset_id: str, data: AuthorizationInput, u=Depends(current), db=Depends(database)):
    a = asset_access(db, u, asset_id, True)
    member(db,u,a.org_id,roles=['owner','admin','analyst'])
    if not data.accepted or a.verified_until <= time.time():
        raise HTTPException(403, 'Verified ownership and explicit authorization are required.')
    scope = {'origin':a.origin,'paths':['/'],'excluded':['all other paths, subdomains and third-party services'],'method':'GET','request_limit':1,'timeout_seconds':5,'type':'root-response-configuration','window_start':time.time()}
    from .multipath import validate_paths
    try:validate_paths(data.paths)
    except ValueError as exc:raise HTTPException(422,str(exc))
    if data.paths!=['/']:scope.update(paths=data.paths,request_limit=len(data.paths),type='explicit-path-response',excluded=['all paths not explicitly listed; all other origins'])
    if data.profile=='api':scope.update(type='api-response-configuration',request_limit=len(data.paths),paths=data.paths)
    auth = Authorization(asset_id=a.id,user_id=u.id,scope=scope,expires=min(a.verified_until,time.time()+data.hours*3600))
    db.add(auth)
    db.flush()
    audit(db,u,'scope.authorized',auth.id,a.org_id)
    db.commit()
    return {'id':auth.id,'scope':scope,'expires':auth.expires}

class JobInput(BaseModel):
    authorization_id: str

@app.post('/assets/{asset_id}/assessments', status_code=201)
def create_job(asset_id: str, data: JobInput, u=Depends(current), db=Depends(database)):
    a=asset_access(db,u,asset_id,True)
    member(db,u,a.org_id,roles=['owner','admin','analyst'])
    # Lock asset to serialize duplicate job creation under PostgreSQL.
    db.scalar(select(Asset).where(Asset.id==a.id).with_for_update())
    paused=db.get(Setting,'scans_paused')
    if paused and paused.value:raise HTTPException(503,'Assessments are paused by the administrator.')
    auth=db.get(Authorization,data.authorization_id)
    if not auth or auth.asset_id!=a.id or auth.revoked or auth.expires<=time.time() or a.verified_until<=time.time():
        raise HTTPException(403,'A current scope authorization for this asset is required.')
    from .windows import require_window
    from .scope import require_supported_scope
    try:
        require_supported_scope(auth.scope,a.origin)
        require_window(auth,time.time())
    except ValueError as exc:raise HTTPException(403,str(exc))
    existing=db.scalar(select(Job).where(Job.asset_id==a.id,Job.status.not_in(['completed','partially_completed','failed','cancelled'])))
    if existing:raise HTTPException(409,'An assessment is already active for this asset.')
    from .models import QueueOutbox
    job=Job(org_id=a.org_id,asset_id=a.id,authorization_id=auth.id)
    db.add(job);db.flush()
    delivery=QueueOutbox(job_id=job.id)
    db.add(delivery);audit(db,u,'assessment.queued',job.id,a.org_id);db.commit()
    from .worker import assess
    try:
        assess.delay(job.id)
        delivery.dispatched=True;delivery.attempts+=1;db.commit()
    except Exception:
        # A crash after broker acceptance can cause redelivery; worker compare-and-swap
        # prevents a second network request. Persistent outbox survives API restart.
        db.rollback()
        delivery=db.scalar(select(QueueOutbox).where(QueueOutbox.job_id==job.id))
        delivery.error='Broker delivery failed; pending durable retry.'
        delivery.attempts+=1;delivery.next_attempt=time.time()+5;db.commit()
    return {'id':job.id,'status':'queued','delivery':'dispatched' if delivery.dispatched else 'pending_retry'}

@app.get('/organizations/{org_id}/assessments')
def list_jobs(org_id: str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    return [{'id':j.id,'asset_id':j.asset_id,'origin':asset_origin(db, Asset, j.asset_id, org_id),'status':j.status,'progress':j.progress,'created':j.created,'error':j.error,'finished':j.finished} for j in db.scalars(select(Job).where(Job.org_id==org_id).order_by(Job.created.desc()).limit(100))]

@app.post('/assessments/{job_id}/cancel')
def cancel_job(job_id: str,u=Depends(current),db=Depends(database)):
    j=db.get(Job,job_id)
    if not j:raise HTTPException(404,'Assessment not found.')
    member(db,u,j.org_id,roles=['owner','admin','analyst'])
    if j.status in ('completed','failed','cancelled'):raise HTTPException(409,'Assessment already finished.')
    j.cancel=True
    if j.status=='queued':
        j.status='cancelled';j.finished=time.time()
        from .models import Retest
        retest=db.scalar(select(Retest).where(Retest.job_id==j.id))
        if retest:
            retest.status='unverified'
            retest.comparison={**retest.comparison,'failure':'Reassessment cancelled before execution; no fix verified.'}
    audit(db,u,'assessment.cancel_requested',j.id,j.org_id);db.commit()
    return {'message':'Cancellation requested. An in-flight request may finish within its timeout.'}

@app.get('/organizations/{org_id}/findings')
def findings(org_id: str,q: str='',severity: str='',status: str='',offset: int=0,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    stmt=select(Finding).where(Finding.org_id==org_id)
    if q:stmt=stmt.where(Finding.title.ilike('%'+q[:100]+'%'))
    if severity:stmt=stmt.where(Finding.severity==severity)
    if status:stmt=stmt.where(Finding.status==status)
    return [{'id':f.id,'asset_id':f.asset_id,'origin':asset_origin(db, Asset, f.asset_id, org_id),'job_id':f.job_id,'rule':f.rule,'title':f.title,'severity':f.severity,'confidence':f.confidence,'evidence':f.evidence,'remediation':f.remediation,'status':f.status,'first_observed':f.created,'last_observed':f.last_observed} for f in db.scalars(stmt.order_by(Finding.last_observed.desc()).offset(max(0,offset)).limit(100))]

class FindingState(BaseModel):
    status: str

@app.patch('/findings/{finding_id}')
def review_finding(finding_id: str,data: FindingState,u=Depends(current),db=Depends(database)):
    f=db.get(Finding,finding_id)
    if not f:raise HTTPException(404,'Finding not found.')
    member(db,u,f.org_id,roles=['owner','admin','analyst'])
    if data.status not in ('open','under_review','accepted_risk','false_positive'):raise HTTPException(422,'Resolution requires a successful retest; choose a review status.')
    f.status=data.status;db.add(FindingHistory(finding_id=f.id,status=f.status));audit(db,u,'finding.reviewed',f.id,f.org_id);db.commit()
    return {'status':f.status}

@app.get('/findings/{finding_id}/explanation')
def explain(finding_id: str,u=Depends(current),db=Depends(database)):
    f=db.get(Finding,finding_id)
    if not f:raise HTTPException(404,'Finding not found.')
    member(db,u,f.org_id)
    from .ai_provider import explain_with_provider
    explanation=explain_with_provider([f.rule])
    from .intelligence.service import grounded_guidance
    explanation['current_approved_knowledge']=grounded_guidance(db,f.title)
    return explanation

@app.get('/assessments/{job_id}/report')
def report(job_id: str,u=Depends(current),db=Depends(database)):
    r=db.scalar(select(Report).where(Report.job_id==job_id))
    if not r:raise HTTPException(404,'Report is not available. Assessment may not have completed.')
    member(db,u,r.org_id)
    from .evidence_vault import require_integrity
    require_integrity(db,r)
    from .reporting import render_pdf
    return StreamingResponse(render_pdf(r.snapshot),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="aegis-{job_id}.pdf"'})

@app.get('/organizations/{org_id}/dashboard')
def dashboard(org_id: str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    def count(model,*conditions):return db.scalar(select(func.count()).select_from(model).where(model.org_id==org_id,*conditions))
    return {'assets':count(Asset),'verified_assets':count(Asset,Asset.verified_until>time.time()),'completed':count(Job,Job.status=='completed'),'active':count(Job,Job.status.in_(['queued','preparing','running','processing_results','generating_report'])),'open_findings':count(Finding,Finding.status.not_in(['resolved','false_positive','accepted_risk'])),'resolved':count(Finding,Finding.status=='resolved'),'severity':{s:count(Finding,Finding.severity==s,Finding.status.not_in(['resolved','false_positive','accepted_risk'])) for s in ['critical','high','medium','low']},'pending_remediation':count(Remediation,Remediation.status.not_in(['closed','rejected'])),'trend':[{'date':j.finished,'count':len(j.observations),'job_id':j.id} for j in db.scalars(select(Job).where(Job.org_id==org_id,Job.status=='completed').order_by(Job.created.desc()).limit(20))], 'activity':[{'action':a.action,'target':a.target,'created':a.created} for a in db.scalars(select(Audit).where(Audit.org_id==org_id).order_by(Audit.created.desc()).limit(20))]}

class RemediationInput(BaseModel):
    finding_id: str

class QuoteInput(BaseModel):
    scope: str = Field(min_length=20,max_length=8000)
    amount_minor: int = Field(default=0,ge=0,le=0)
    currency: str = Field(pattern=r'^[A-Z]{3}$',default='EGP')

class DecisionInput(BaseModel):
    accept: bool

class TaskInput(BaseModel):
    status: str
    assigned_user_id: str | None = None

class MessageInput(BaseModel):
    body: str = Field(min_length=1,max_length=8000)
    internal: bool = False

def remediation_dict(r):
    return {'id':r.id,'org_id':r.org_id,'finding_id':r.finding_id,'status':r.status,'estimate':r.estimate,'scope':r.scope,'amount_minor':None,'currency':r.currency,'accepted_at':r.accepted_at,'assigned_user_id':r.assigned_user_id,'payment_status':'disabled — no payment collected'}

def remediation_access(db,u,request_id,write=False):
    r=db.get(Remediation,request_id)
    if not r:raise HTTPException(404,'Remediation request not found.')
    member(db,u,r.org_id,write=write)
    return r

@app.post('/remediations',status_code=201)
def request_fix(data:RemediationInput,u=Depends(current),db=Depends(database)):
    f=db.get(Finding,data.finding_id)
    if not f:raise HTTPException(404,'Finding not found.')
    member(db,u,f.org_id,roles=['owner','admin','analyst'])
    db.scalar(select(Asset).where(Asset.id==f.asset_id).with_for_update())
    db.refresh(f)
    if f.status in ('resolved','false_positive','accepted_risk'):raise HTTPException(409,'Finding is not eligible for remediation.')
    existing=db.scalar(select(Remediation).where(Remediation.finding_id==f.id,Remediation.status.not_in(['rejected','closed'])))
    if existing:raise HTTPException(409,'A remediation request is already open.')
    r=Remediation(org_id=f.org_id,finding_id=f.id,estimate='Preliminary: 1–4 engineering hours for configuration review and change validation. Developer access and one retest required. Complexity and effort must be confirmed by an engineer; this is not a formal quotation.')
    db.add(r);db.flush();f.status='remediation_requested';db.add(FindingHistory(finding_id=f.id,status=f.status));audit(db,u,'remediation.requested',r.id,r.org_id);db.commit()
    return remediation_dict(r)

@app.get('/organizations/{org_id}/remediations')
def remediations(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    return [{**remediation_dict(r),'asset_id':f.asset_id,'finding_title':f.title} for r,f in db.execute(select(Remediation,Finding).join(Finding,Finding.id==Remediation.finding_id).where(Remediation.org_id==org_id,Finding.org_id==org_id).order_by(Remediation.created.desc()).limit(100))]

@app.post('/admin/remediations/{request_id}/quote')
def quote(request_id:str,data:QuoteInput,u=Depends(current),db=Depends(database)):
    admin(u)
    r=db.scalar(select(Remediation).where(Remediation.id==request_id).with_for_update())
    if not r:raise HTTPException(404,'Request not found.')
    if r.status not in ('requested','quoted'):raise HTTPException(409,'Accepted or closed quotation cannot be edited.')
    r.scope=data.scope;r.amount=None;r.status='quoted';audit(db,u,'quotation.issued',r.id,r.org_id);db.commit()
    return remediation_dict(r)

@app.post('/remediations/{request_id}/decision')
def quote_decision(request_id:str,data:DecisionInput,u=Depends(current),db=Depends(database)):
    r=remediation_access(db,u,request_id,True)
    member(db,u,r.org_id,roles=['owner','admin'])
    db.refresh(r,with_for_update=True)
    if r.status!='quoted':raise HTTPException(409,'Only a formal quoted scope can be accepted or rejected.')
    r.status='accepted' if data.accept else 'rejected';r.accepted_at=time.time() if data.accept else None
    audit(db,u,'quotation.'+r.status,r.id,r.org_id);db.commit()
    return remediation_dict(r)

@app.patch('/remediations/{request_id}/task')
def task_update(request_id:str,data:TaskInput,u=Depends(current),db=Depends(database)):
    r=remediation_access(db,u,request_id,True)
    member(db,u,r.org_id,roles=['owner','admin','engineer'])
    db.refresh(r,with_for_update=True)
    transitions={'accepted':['in_progress'],'in_progress':['ready_for_retest'],'ready_for_retest':['in_progress','closed']}
    if data.status not in transitions.get(r.status,[]):raise HTTPException(409,'Invalid task transition. Customer scope approval is required before work.')
    if data.assigned_user_id:
        m=db.scalar(select(Membership).where(Membership.org_id==r.org_id,Membership.user_id==data.assigned_user_id,Membership.role.in_(['owner','admin','engineer'])))
        if not m:raise HTTPException(422,'Assign a remediation engineer or administrator in this workspace.')
        r.assigned_user_id=data.assigned_user_id
    if data.status=='closed':
        from .models import Retest
        latest=db.scalar(select(Retest).where(Retest.remediation_id==r.id).order_by(Retest.created.desc()))
        if not latest or latest.status!='verified_original' or db.get(Finding,r.finding_id).status!='resolved':
            raise HTTPException(409,'A customer-approved full reassessment must verify the original observation before closure.')
        if latest.comparison.get('new') or latest.comparison.get('unverified') or latest.comparison.get('unresolved') or latest.comparison.get('advisories'):
            raise HTTPException(409,'Regression or unverified findings remain. Review and resolve them before closing this complete remediation workflow.')
    r.status=data.status;audit(db,u,'remediation.'+r.status,r.id,r.org_id);db.commit()
    return remediation_dict(r)

@app.get('/remediations/{request_id}/messages')
def messages(request_id:str,u=Depends(current),db=Depends(database)):
    r=remediation_access(db,u,request_id)
    m=member(db,u,r.org_id)
    stmt=select(Message).where(Message.remediation_id==r.id)
    if m.role not in ('owner','admin','engineer'):stmt=stmt.where(Message.internal.is_(False))
    return [{'id':x.id,'body':x.body,'internal':x.internal,'created':x.created,'author':db.get(User,x.user_id).email} for x in db.scalars(stmt.order_by(Message.created).limit(200))]

@app.post('/remediations/{request_id}/messages')
def post_message(request_id:str,data:MessageInput,u=Depends(current),db=Depends(database)):
    r=remediation_access(db,u,request_id,True)
    if data.internal:member(db,u,r.org_id,roles=['owner','admin','engineer'])
    message=Message(org_id=r.org_id,remediation_id=r.id,user_id=u.id,body=data.body,internal=data.internal)
    db.add(message);audit(db,u,'remediation.message',r.id,r.org_id);db.commit()
    return {'message':'Message saved.'}

class PauseInput(BaseModel):
    paused: bool

@app.post('/admin/assessment-control')
def pause(data:PauseInput,u=Depends(current),db=Depends(database)):
    admin(u)
    flag=db.get(Setting,'scans_paused')
    if not flag:flag=Setting(key='scans_paused',value=data.paused);db.add(flag)
    else:flag.value=data.paused
    if data.paused:
        for j in db.scalars(select(Job).where(Job.status.in_(['queued','preparing','running','processing_results','generating_report']))):
            j.cancel=True
            if j.status=='queued':
                j.status='cancelled';j.finished=time.time()
                from .models import Retest
                retest=db.scalar(select(Retest).where(Retest.job_id==j.id))
                if retest:
                    retest.status='unverified'
                    retest.comparison={**retest.comparison,'failure':'Reassessment cancelled before execution; no fix verified.'}
    audit(db,u,'platform.scans_paused' if data.paused else 'platform.scans_resumed','platform');db.commit()
    return {'paused':flag.value}

@app.get('/admin/overview')
def admin_overview(u=Depends(current),db=Depends(database)):
    admin(u)
    paused=db.get(Setting,'scans_paused')
    from .ai_provider import provider_state
    return {'organizations':[{'id':o.id,'name':o.name} for o in db.scalars(select(Organization).limit(100))], 'users':db.scalar(select(func.count()).select_from(User)),'jobs':{s:db.scalar(select(func.count()).select_from(Job).where(Job.status==s)) for s in ['queued','running','failed','completed','cancelled']},'remediations':[remediation_dict(r) for r in db.scalars(select(Remediation).order_by(Remediation.created.desc()).limit(100))], 'audit':[{'action':a.action,'target':a.target,'created':a.created} for a in db.scalars(select(Audit).order_by(Audit.created.desc()).limit(100))], 'scans_paused':bool(paused and paused.value),'payments_enabled':False,'ai_mode':provider_state()['mode'],'email_host':os.getenv('SMTP_HOST','localhost'),'reports':db.scalar(select(func.count()).select_from(Report))}

@app.get('/admin/health')
def admin_health(u=Depends(current)):
    admin(u)
    from .worker import celery
    import redis
    try:
        r=redis.Redis.from_url(os.getenv('REDIS_URL','redis://localhost:6379/0'),socket_connect_timeout=2,socket_timeout=2)
        r.ping();queue={'reachable':True,'pending_messages':r.llen('celery')}
    except Exception:queue={'reachable':False,'pending_messages':None}
    try:workers=celery.control.inspect(timeout=1).ping() or {}
    except Exception:workers={}
    return {'queue':queue,'workers':workers,'storage':'database snapshots; PDF rendered on demand','ai':'deterministic; no external provider connected'}

@app.post('/admin/recover-stale-jobs')
def recover(u=Depends(current),db=Depends(database)):
    admin(u)
    jobs=db.scalars(select(Job).where(Job.status.in_(['queued','preparing','running','processing_results','generating_report']),Job.created<time.time()-300)).all()
    from .models import Retest, AssessmentSchedule
    from .intelligence.service import notify
    for j in jobs:
        j.cancel=True;j.status='failed';j.error='Stale job marked failed by administrator. Create a new authorized assessment.';j.finished=time.time()
        retest=db.scalar(select(Retest).where(Retest.job_id==j.id))
        if retest:
            retest.status='unverified';retest.comparison={**retest.comparison,'failure':'Stale reassessment recovered; no fix verified.'}
        for schedule in db.scalars(select(AssessmentSchedule).where(AssessmentSchedule.last_job_id==j.id)):schedule.status='failed'
        notify(db,j.org_id,'assessment_failed','job-failure:'+j.id,'Assessment failed','Stale assessment recovered; no clean result or verified fix is implied.',j.id)
        audit(db,u,'assessment.recovered',j.id,j.org_id)
    db.commit()
    return {'recovered':len(jobs)}

from .intelligence.routes import router as intelligence_router
app.include_router(intelligence_router)
from .firebase_identity import router as firebase_router
app.include_router(firebase_router)
from .team import router as team_router
app.include_router(team_router)
from .support import router as support_router
app.include_router(support_router)
from .mfa import router as mfa_router
app.include_router(mfa_router)

class RemediationSelection(BaseModel):
    selection: str = Field(default='all',pattern=r'^(all|critical|critical_high)$')

@app.post('/assets/{asset_id}/request-remediation', status_code=201)
def request_asset_remediation(asset_id: str, data:RemediationSelection|None=None, u=Depends(current), db=Depends(database)):
    """One click requests engineer review of eligible findings, never applies fixes."""
    a = asset_access(db, u, asset_id, True)
    member(db,u,a.org_id,roles=['owner','admin','analyst'])
    # Serialize requests for the same asset on PostgreSQL to avoid duplicate open tickets.
    db.scalar(select(Asset).where(Asset.id==a.id).with_for_update())
    selection=data.selection if data else 'all'
    stmt=select(Finding).where(Finding.asset_id==a.id,Finding.org_id==a.org_id,Finding.status.not_in(['resolved','false_positive','accepted_risk']))
    if selection!='all':stmt=stmt.where(Finding.severity.in_(['critical'] if selection=='critical' else ['critical','high']))
    findings=db.scalars(stmt.order_by(Finding.id)).all()
    ids=[];created=0;reused=0
    for f in findings:
        r=db.scalar(select(Remediation).where(Remediation.finding_id==f.id,Remediation.status.not_in(['closed','rejected'])))
        if not r:
            created+=1
            r=Remediation(org_id=a.org_id,finding_id=f.id,estimate='Preliminary engineering review required. Scope, compatibility, staging tests and rollback must be agreed before any change. No payment required or collected.')
            db.add(r);db.flush()
            f.status='remediation_requested'
            db.add(FindingHistory(finding_id=f.id,status=f.status))
            audit(db,u,'remediation.requested',r.id,a.org_id)
        else:reused+=1
        ids.append(r.id)
    db.commit()
    return {'request_ids':ids,'count':len(ids),'created':created,'reused':reused,'selection':selection,'applied':False,
        'estimate':'Preliminary; an engineer must assess compatibility, access, staging tests and retesting before quoting effort.',
        'message':('Engineering review requested. Existing open requests reused. No website changes made and no payment collected.' if ids else 'No eligible findings match this selection. No remediation request or website change was made.')}

@app.get('/remediations/{request_id}/document/{kind}')
def remediation_document(request_id:str,kind:str,u=Depends(current),db=Depends(database)):
    from .models import Retest
    from .reporting import render_remediation_document
    if kind not in ('quotation','progress','completion'):
        raise HTTPException(422,'Choose quotation, progress or completion.')
    r=remediation_access(db,u,request_id)
    f=db.get(Finding,r.finding_id);a=db.get(Asset,f.asset_id)
    latest=db.scalar(select(Retest).where(Retest.remediation_id==r.id).order_by(Retest.created.desc()))
    if kind=='quotation' and not r.scope:
        raise HTTPException(409,'A formal quotation has not been issued.')
    if kind=='completion':
        if r.status!='closed' or f.status!='resolved' or not latest or latest.status!='verified_original':
            raise HTTPException(409,'Verified full reassessment and closure required for completion summary.')
        if any(latest.comparison.get(k) for k in ('new','unverified','unresolved','advisories')):
            raise HTTPException(409,'Reassessment gaps prevent a completion summary.')
        newest=db.scalar(select(Job).where(Job.asset_id==a.id).order_by(Job.created.desc()))
        if not newest or newest.id!=latest.job_id:
            raise HTTPException(409,'A newer assessment exists. Review its evidence before issuing completion.')
        job=db.get(Job,latest.job_id)
        if not job or job.status!='completed' or not db.scalar(select(Report).where(Report.job_id==job.id)):
            raise HTTPException(409,'Completed reassessment report is required.')
    data={**remediation_dict(r),'organization':db.get(Organization,r.org_id).name,
        'origin':a.origin,'finding_title':f.title,
        'retest':{'status':latest.status,'job_id':latest.job_id,'comparison':latest.comparison} if latest else None}
    return StreamingResponse(render_remediation_document(data,kind),media_type='application/pdf',
        headers={'Content-Disposition':f'attachment; filename="aegis-{kind}-{r.id}.pdf"'})

from .attachments import router as attachments_router
app.include_router(attachments_router)
from .attachments import AttachmentBodyLimit
app.add_middleware(AttachmentBodyLimit)

from .notifications import router as notifications_router
app.include_router(notifications_router)

from .account import router as account_router
app.include_router(account_router)

from .ownership_transfer import router as ownership_transfer_router
app.include_router(ownership_transfer_router)

from .operations import router as operations_router
app.include_router(operations_router)

from .finding_browser import router as finding_browser_router
app.include_router(finding_browser_router)

from .remediation_browser import router as remediation_browser_router
app.include_router(remediation_browser_router)

from .repositories import router as repositories_router
app.include_router(repositories_router)

from .discovery import router as discovery_router
app.include_router(discovery_router)
from .health_monitoring import router as health_router
app.include_router(health_router)

from .smartverify import router as smartverify_router
app.include_router(smartverify_router)
from .cloudflare_verify import router as cloudflare_verify_router
app.include_router(cloudflare_verify_router)
from .launch_guard import router as launch_guard_router
app.include_router(launch_guard_router)
from .agency import router as agency_router
app.include_router(agency_router)

from .email_alerts import router as email_alerts_router
app.include_router(email_alerts_router)

from .autofix_recovery import router as autofix_recovery_router
app.include_router(autofix_recovery_router)

from .crm import router as crm_router
from .evidence_vault import router as evidence_vault_router
app.include_router(crm_router)
app.include_router(evidence_vault_router)

from .fastfix import router as fastfix_router
app.include_router(fastfix_router)
