"""Explicit GitHub consent, bounded configuration proposals and reviewed PRs."""
import base64
import difflib
import json
import math
import re
from decimal import Decimal
import secrets
import time
from urllib.parse import quote
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select,update
from . import github_client as gh
from .auth import current,member,audit,digest,admin
from .db import database
from .models import GitHubState,GitHubConnection,RepositoryPatch,Remediation,Finding,MfaState,Setting
router=APIRouter(tags=['Authorized repositories'])

def call(path,token,method='GET',body=None):
    try:return gh.request('api.github.com',path,method,token,body)
    except gh.GitHubError:raise HTTPException(502,'GitHub request failed. No successful change is implied.')

def connection(db,u,cid,write=False):
    c=db.get(GitHubConnection,cid)
    if not c:raise HTTPException(404,'Connection not found.')
    member(db,u,c.org_id,roles=['owner','admin'] if write else None)
    # A user token is never silently delegated to another workspace member.
    if c.user_id!=u.id:raise HTTPException(403,'Use your own GitHub connection.')
    if c.revoked or c.expires<=time.time():raise HTTPException(409,'Reconnect GitHub; authorization expired or was revoked.')
    try:token=gh.cipher().decrypt(c.encrypted_token.encode()).decode()
    except Exception:raise HTTPException(503,'Repository credentials unavailable.')
    return c,token

def repo_path(repository):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}/[A-Za-z0-9_.-]{1,100}',repository) or repository.endswith('/.') or repository.endswith('/..'):
        raise HTTPException(422,'Use an owner/repository identifier.')
    return '/repos/'+repository

class Consent(BaseModel):
    accepted:bool
class Complete(BaseModel):
    state:str=Field(min_length=20,max_length=200)
    code:str=Field(min_length=1,max_length=500)

@router.post('/organizations/{org_id}/github/start')
def start(org_id:str,data:Consent,u=Depends(current),db=Depends(database)):
    member(db,u,org_id,roles=['owner','admin'])
    from .main import throttle
    throttle('github-connect:'+u.id)
    if not data.accepted:raise HTTPException(422,'Explicit repository connection consent required.')
    state=secrets.token_urlsafe(32)
    try:url=gh.authorization_url(state)
    except Exception:raise HTTPException(503,'GitHub App configuration is required.')
    db.add(GitHubState(org_id=org_id,user_id=u.id,digest=digest(state),expires=time.time()+600))
    audit(db,u,'github.authorization_started',org_id,org_id);db.commit()
    return {'url':url,'expires_in':600}

@router.post('/organizations/{org_id}/github/complete')
def complete(org_id:str,data:Complete,u=Depends(current),db=Depends(database)):
    member(db,u,org_id,roles=['owner','admin'])
    row=db.scalar(select(GitHubState).where(GitHubState.org_id==org_id,GitHubState.user_id==u.id,GitHubState.digest==digest(data.state)))
    if not row:raise HTTPException(403,'Invalid connection state.')
    claimed=db.execute(update(GitHubState).where(GitHubState.id==row.id,GitHubState.used.is_(False),GitHubState.expires>time.time()).values(used=True))
    db.commit()
    if not claimed.rowcount:raise HTTPException(409,'Connection state expired or was already used. Start again.')
    try:
        token,expires,identity=gh.exchange(data.code)
        encrypted=gh.cipher().encrypt(token.encode()).decode()
    except Exception:raise HTTPException(502,'GitHub authorization failed. Start again.')
    c=GitHubConnection(org_id=org_id,user_id=u.id,account_id=str(identity['id']),login=str(identity.get('login',''))[:100],encrypted_token=encrypted,expires=time.time()+expires)
    db.add(c);db.flush();audit(db,u,'github.connected',c.id,org_id);db.commit()
    return {'id':c.id,'login':c.login,'expires':c.expires}

@router.get('/organizations/{org_id}/github')
def connections(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    return [{'id':c.id,'login':c.login,'expires':c.expires,'revoked':c.revoked} for c in db.scalars(select(GitHubConnection).where(GitHubConnection.org_id==org_id,GitHubConnection.user_id==u.id))]

@router.delete('/github/connections/{cid}')
def revoke(cid:str,u=Depends(current),db=Depends(database)):
    c=db.get(GitHubConnection,cid)
    if not c:raise HTTPException(404,'Connection not found.')
    member(db,u,c.org_id,roles=['owner','admin'])
    c.revoked=True;c.encrypted_token='';audit(db,u,'github.disconnected',c.id,c.org_id);db.commit()
    return {'revoked':True,'note':'AEGIS credential removed. Revoke the GitHub App installation in GitHub to remove provider access.'}

@router.get('/github/connections/{cid}/repositories')
def repositories(cid:str,page:int=1,u=Depends(current),db=Depends(database)):
    _,token=connection(db,u,cid)
    if not 1<=page<=100:raise HTTPException(422,'Invalid page.')
    rows=call('/user/repos?per_page=30&page='+str(page),token)
    if not isinstance(rows,list):raise HTTPException(502,'Invalid repository listing.')
    return [{'name':r['full_name'],'default_branch':r['default_branch']} for r in rows if r.get('permissions',{}).get('push') and not r.get('archived')]

def propose_nosniff(content):
    """Single reviewed transformation. Never evaluates JS or executes repo scripts."""
    if not isinstance(content,str) or len(content.encode('utf-8'))>65536:raise ValueError('Configuration too large.')
    def unique_object(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:raise ValueError('Duplicate JSON keys require manual review.')
            obj[key]=value
        return obj
    def reject_constant(value):raise ValueError('Non-finite JSON values require manual review.')
    def exact_float(value):
        # JSON can overflow to Infinity or silently lose decimal precision.
        number=float(value)
        if not math.isfinite(number) or Decimal(str(number))!=Decimal(value):
            raise ValueError('Non-round-trippable JSON numbers require manual review.')
        return number
    parse_options={'object_pairs_hook':unique_object,'parse_constant':reject_constant,'parse_float':exact_float}
    config=json.loads(content or '{}',**parse_options)
    if not isinstance(config,dict):raise ValueError('Expected a JSON object.')
    headers=config.setdefault('headers',[])
    if not isinstance(headers,list):raise ValueError('Invalid headers configuration.')
    for entry in headers:
        if not isinstance(entry,dict) or not isinstance(entry.get('headers'),list):raise ValueError('Invalid header rule.')
        for header in entry['headers']:
            if not isinstance(header,dict) or not isinstance(header.get('key'),str):raise ValueError('Invalid header entry.')
            if header['key'].lower()=='x-content-type-options':raise ValueError('Existing policy requires manual review; no overwrite proposed.')
    headers.append({'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'}]})
    result=json.dumps(config,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if len(result.encode('utf-8'))>65536:
        raise ValueError('Proposed configuration exceeds the safe size limit.')
    # Structural regression check: removing our exact addition restores every original field.
    verified=json.loads(result,**parse_options);verified['headers'].pop()
    before=json.loads(content or '{}',**parse_options);before.setdefault('headers',[])
    if verified!=before:raise ValueError('Configuration preservation test failed.')
    return result

class Proposal(BaseModel):
    connection_id:str
    repository:str
    remediation_id:str
    accepted:bool

@router.post('/repository-patches')
def propose(data:Proposal,u=Depends(current),db=Depends(database)):
    c,token=connection(db,u,data.connection_id,write=True)
    r=db.get(Remediation,data.remediation_id)
    if not r or r.org_id!=c.org_id:raise HTTPException(404,'Remediation not found in this workspace.')
    if not data.accepted:raise HTTPException(422,'Repository analysis consent required.')
    if r.status not in ('accepted','in_progress','ready_for_retest'):raise HTTPException(409,'Accept the remediation scope before proposing a patch.')
    finding=db.get(Finding,r.finding_id)
    if finding.rule.split('@')[0]!='header.nosniff':raise HTTPException(409,'This finding has no supported automatic patch generator; engineer review required.')
    root=repo_path(data.repository);repo=call(root,token)
    if not repo.get('permissions',{}).get('push') or repo.get('archived'):raise HTTPException(403,'Repository write authorization required.')
    branch=repo['default_branch'];head=call(root+'/git/ref/heads/'+quote(branch,safe=''),token)['object']['sha']
    file=call(root+'/contents/vercel.json?ref='+quote(head,safe=''),token)
    if file.get('type')!='file' or file.get('encoding')!='base64' or file.get('size',65537)>65536:raise HTTPException(409,'Only an existing bounded vercel.json is supported.')
    try:
        original=base64.b64decode(file['content']).decode('utf-8');proposed=propose_nosniff(original)
    except (ValueError,KeyError,UnicodeError):raise HTTPException(409,'Configuration needs engineer review; no change proposed.')
    diff=''.join(difflib.unified_diff(original.splitlines(True),proposed.splitlines(True),fromfile='a/vercel.json',tofile='b/vercel.json',n=0))
    patch=RepositoryPatch(org_id=c.org_id,connection_id=c.id,remediation_id=r.id,repository=data.repository,base_branch=branch,base_sha=head,file_sha=file['sha'],proposed_content=gh.cipher().encrypt(proposed.encode()).decode(),diff=gh.cipher().encrypt(diff.encode()).decode(),test_evidence={'configuration_preserved':True,'json_valid':True,'application_tests':'not run','staging':'not verified'})
    db.add(patch);db.flush()
    from .autofix_recovery import create_backup
    create_backup(db,patch,original,proposed)
    audit(db,u,'github.patch_proposed',patch.id,c.org_id);db.commit()
    return patch_view(patch)

def patch_view(p):
    try:diff=gh.cipher().decrypt(p.diff.encode()).decode()
    except Exception:raise HTTPException(503,'Proposal encryption key unavailable. Restore the configured key; no repository change performed.')
    return {'id':p.id,'repository':p.repository,'base_branch':p.base_branch,'base_sha':p.base_sha,'diff':diff,'status':p.status,'tests':p.test_evidence,'pull_number':p.pull_number,'remediation_id':p.remediation_id}


@router.get('/organizations/{org_id}/repository-patches')
def patches(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id,roles=['owner','admin'])
    return [patch_view(p) for p in db.scalars(select(RepositoryPatch).join(GitHubConnection,RepositoryPatch.connection_id==GitHubConnection.id).where(RepositoryPatch.org_id==org_id,GitHubConnection.user_id==u.id).order_by(RepositoryPatch.created.desc()).limit(100))]

class Approval(BaseModel):
    accepted:bool
    mfa_code:str=Field(min_length=6,max_length=64)

@router.post('/repository-patches/{patch_id}/pull-request')
def create_pr(patch_id:str,data:Approval,u=Depends(current),db=Depends(database)):
    p=db.scalar(select(RepositoryPatch).where(RepositoryPatch.id==patch_id).with_for_update())
    if not p:raise HTTPException(404,'Patch not found.')
    member(db,u,p.org_id,roles=['owner','admin'])
    remediation=db.get(Remediation,p.remediation_id)
    paused=db.get(Setting,'repository_writes_paused')
    if (paused and paused.value) or remediation.status not in ('accepted','in_progress','ready_for_retest'):raise HTTPException(409,'Repository publication is paused or remediation scope is inactive.')
    if not data.accepted or p.status!='review_required':raise HTTPException(409,'Explicit approval of a pending diff is required.')
    mfa=db.get(MfaState,u.id)
    if not mfa or not mfa.enabled:raise HTTPException(403,'Enable authenticator MFA before authorizing repository writes.')
    from .mfa import enforce
    enforce(db,u,data.mfa_code)
    _,token=connection(db,u,p.connection_id,write=True);root=repo_path(p.repository)
    head=call(root+'/git/ref/heads/'+quote(p.base_branch,safe=''),token)['object']['sha']
    if head!=p.base_sha:raise HTTPException(409,'Base branch changed; generate and review a fresh proposal.')
    # Persist intent before external writes. An ambiguous failure is never retried silently.
    p.status='publishing';p.approved_by=u.id;audit(db,u,'github.pr_approved',p.id,p.org_id);db.commit()
    branch='aegis/review-'+p.id
    try:
        call(root+'/git/refs',token,'POST',{'ref':'refs/heads/'+branch,'sha':p.base_sha})
        call(root+'/contents/vercel.json',token,'PUT',{'message':'Propose reviewed browser content-type protection','branch':branch,'sha':p.file_sha,'content':base64.b64encode(gh.cipher().decrypt(p.proposed_content.encode())).decode()})
        result=call(root+'/pulls',token,'POST',{'title':'Review browser content-type protection','head':branch,'base':p.base_branch,'draft':True,'body':'AEGIS reviewed configuration proposal. JSON and field-preservation checks passed. Application CI and staging validation remain required. No merge, deployment, or verified remediation is implied.'})
        p.pull_number=int(result['number']);p.status='pull_request_open';audit(db,u,'github.pr_created',p.id,p.org_id);db.commit()
    except Exception:
        p.status='publication_unverified';db.commit()
        raise HTTPException(502,'Publication incomplete or uncertain. Inspect the AEGIS review branch in GitHub before retrying; no merge or deployment performed.')
    return patch_view(p)

@router.post('/repository-patches/{patch_id}/refresh')
def refresh(patch_id:str,u=Depends(current),db=Depends(database)):
    p=db.get(RepositoryPatch,patch_id)
    if not p:raise HTTPException(404,'Patch not found.')
    member(db,u,p.org_id)
    if not p.pull_number:raise HTTPException(409,'No confirmed pull request exists.')
    _,token=connection(db,u,p.connection_id)
    root=repo_path(p.repository);pr=call(root+'/pulls/'+str(p.pull_number),token)
    p.status='merged_awaiting_deployment' if pr.get('merged') else 'closed_without_merge' if pr.get('state')=='closed' else 'pull_request_open'
    sha=pr['head']['sha'];checks=call(root+'/commits/'+quote(sha,safe='')+'/check-runs?per_page=100',token)
    runs=checks.get('check_runs',[])
    p.test_evidence={**p.test_evidence,'github_checks':[{'name':str(c.get('name',''))[:200],'status':c.get('status'),'conclusion':c.get('conclusion')} for c in runs],'ci_complete':bool(runs) and checks.get('total_count',0)<=100 and all(c.get('status')=='completed' and c.get('conclusion')=='success' for c in runs)}
    audit(db,u,'github.pr_status_refreshed',p.id,p.org_id);db.commit()
    return patch_view(p)

@router.post('/admin/repository-control')
def repository_control(data:Consent,u=Depends(current),db=Depends(database)):
    admin(u)
    setting=db.get(Setting,'repository_writes_paused')
    if not setting:setting=Setting(key='repository_writes_paused',value=data.accepted);db.add(setting)
    else:setting.value=data.accepted
    audit(db,u,'github.publication_pause_changed','repository_writes_paused');db.commit()
    return {'paused':setting.value}

@router.get('/admin/repository-control')
def repository_control_status(u=Depends(current),db=Depends(database)):
    admin(u)
    setting=db.get(Setting,'repository_writes_paused')
    return {'paused':bool(setting and setting.value)}
