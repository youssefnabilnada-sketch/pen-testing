import base64
import json
import time
from urllib.parse import urlsplit,parse_qs
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select
from fastapi.testclient import TestClient
from aegis.main import app
from aegis import github_client as gh
from aegis.db import Session
from aegis.models import GitHubConnection,RepositoryPatch,Finding,MfaState,Remediation
from aegis.repositories import propose_nosniff
from conftest import signup
from test_monitoring_regression import setup_fix

@pytest.fixture
def github(monkeypatch):
    for k,v in {'GITHUB_ENABLED':'true','GITHUB_CLIENT_ID':'fixture-app','GITHUB_CLIENT_SECRET':'fixture-secret','GITHUB_REDIRECT_URI':'https://aegis.test/console','GITHUB_TOKEN_KEY':Fernet.generate_key().decode()}.items():monkeypatch.setenv(k,v)
    monkeypatch.setattr(gh,'exchange',lambda code:('fixture-private-token',3600,{'id':123,'login':'fixture-user'}))
    calls=[]
    def request(host,path,method='GET',token=None,body=None):
        calls.append((path,method,body))
        if path.startswith('/user/repos'):return [{'full_name':'owned/site','default_branch':'main','permissions':{'push':True}}]
        if path=='/repos/owned/site':return {'default_branch':'main','permissions':{'push':True}}
        if '/git/ref/heads/' in path:return {'object':{'sha':'a'*40}}
        if '/contents/vercel.json' in path and method=='GET':return {'type':'file','encoding':'base64','content':base64.b64encode(b'{"version":2}').decode(),'sha':'b'*40,'size':13}
        if path.endswith('/pulls') and method=='POST':return {'number':7}
        if path.endswith('/pulls/7'):return {'merged':True,'head':{'sha':'c'*40}}
        if '/check-runs' in path:return {'total_count':1,'check_runs':[{'name':'fixture tests','status':'completed','conclusion':'success'}]}
        if method in ('POST','PUT'):return {}
        raise AssertionError(path)
    monkeypatch.setattr(gh,'request',request)
    return calls

def connect(client,org):
    started=client.post(f'/organizations/{org}/github/start',json={'accepted':True})
    assert started.status_code==200,started.text
    state=parse_qs(urlsplit(started.json()['url']).query)['state'][0]
    result=client.post(f'/organizations/{org}/github/complete',json={'state':state,'code':'fixture-code'})
    assert result.status_code==200,result.text
    return result.json()['id'],state

def test_connection_state_tenant_expiry_and_cipher(client,mail,github):
    org=signup(client,mail);cid,state=connect(client,org)
    assert client.post(f'/organizations/{org}/github/complete',json={'state':state,'code':'again'}).status_code==409
    with Session() as db:
        c=db.get(GitHubConnection,cid);assert 'fixture-private-token' not in c.encrypted_token
    outsider=TestClient(app);signup(outsider,mail,'other@example.test')
    assert outsider.get(f'/github/connections/{cid}/repositories').status_code==403
    assert client.get(f'/github/connections/{cid}/repositories').json()[0]['name']=='owned/site'
    assert client.delete(f'/github/connections/{cid}').status_code==200
    assert client.get(f'/github/connections/{cid}/repositories').status_code==409

@pytest.mark.parametrize('bad',['[]','{"headers":{}}','{"headers":[{}]}','{"headers":[{"headers":[{"key":"X-Content-Type-Options","value":"none"}]}]}'])
def test_unsupported_config_rejected(bad):
    with pytest.raises(ValueError):propose_nosniff(bad)

def test_patch_preserves_configuration_without_executing_code():
    before={'rewrites':[{'source':'/','destination':'/home'}],'version':2}
    result=json.loads(propose_nosniff(json.dumps(before)))
    assert result['rewrites']==before['rewrites']
    assert result['headers'][0]['headers'][0]['value']=='nosniff'

def patch_setup(client,mail,monkeypatch,github):
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    with Session() as db:
        f=db.scalar(select(Finding).where(Finding.asset_id==asset,Finding.rule=='header.nosniff'))
        db.get(Remediation,rid).finding_id=f.id;db.commit()
    cid,_=connect(client,org)
    p=client.post('/repository-patches',json={'connection_id':cid,'repository':'owned/site','remediation_id':rid,'accepted':True})
    assert p.status_code==200,p.text
    return org,rid,cid,p.json()['id']

def test_proposal_review_mfa_pr_and_retest_separation(client,mail,monkeypatch,github):
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    view=client.get(f'/organizations/{org}/repository-patches').json()[0]
    assert '+      "source": "/(.*)"' in view['diff']
    assert view['tests']['application_tests']=='not run'
    assert not any(method in ('POST','PUT') for _,method,_ in github)
    assert client.post(f'/repository-patches/{pid}/pull-request',json={'accepted':True,'mfa_code':'123456'}).status_code==403
    with Session() as db:
        c=db.get(GitHubConnection,cid)
        db.add(MfaState(user_id=c.user_id,secret='fixture',enrollment_session='fixture-session',enabled=True,expires=time.time()+300,last_counter=-1));db.commit()
    monkeypatch.setattr('aegis.mfa.enforce',lambda *args:None) # isolated provider fixture; MFA itself has separate real OTP tests
    result=client.post(f'/repository-patches/{pid}/pull-request',json={'accepted':True,'mfa_code':'123456'})
    assert result.status_code==200,result.text
    assert result.json()['pull_number']==7
    writes=[(path,method,body) for path,method,body in github if method in ('POST','PUT')]
    assert writes[0][2]['ref']=='refs/heads/aegis/review-'+pid
    assert writes[1][2]['branch']!='main'
    assert writes[2][2]['draft'] is True
    assert client.post(f'/repository-patches/{pid}/pull-request',json={'accepted':True,'mfa_code':'123456'}).status_code==409
    refreshed=client.post(f'/repository-patches/{pid}/refresh').json()
    assert refreshed['status']=='merged_awaiting_deployment'
    assert refreshed['tests']['ci_complete'] is True
    assert client.get(f'/remediations/{rid}/retests').json()==[] # a merge is never deployment evidence

def test_unavailable_provider_does_not_publish(client,mail,monkeypatch,github):
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    monkeypatch.setattr(gh,'request',lambda *a,**kw:(_ for _ in ()).throw(gh.GitHubError('fixture outage')))
    assert client.get(f'/github/connections/{cid}/repositories').status_code==502
    with Session() as db:assert db.get(RepositoryPatch,pid).status=='review_required'

def test_oauth_wrong_workspace_and_expired_token(client,mail,github):
    org=signup(client,mail);cid,state=connect(client,org)
    other=client.post('/organizations',json={'name':'Second workspace'}).json()['id']
    assert client.post(f'/organizations/{other}/github/complete',json={'state':state,'code':'fixture'}).status_code==403
    with Session() as db:db.get(GitHubConnection,cid).expires=0;db.commit()
    assert client.get(f'/github/connections/{cid}/repositories').status_code==409

@pytest.mark.parametrize('scenario',['base_changed','write_failure'])
def test_stale_or_uncertain_publication_is_not_success(client,mail,monkeypatch,github,scenario):
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    with Session() as db:
        c=db.get(GitHubConnection,cid)
        db.add(MfaState(user_id=c.user_id,secret='fixture',enrollment_session='fixture-session',enabled=True,expires=time.time()+300,last_counter=-1));db.commit()
    monkeypatch.setattr('aegis.mfa.enforce',lambda *args:None)
    original=gh.request
    def altered(host,path,method='GET',token=None,body=None):
        if scenario=='base_changed' and '/git/ref/heads/' in path:return {'object':{'sha':'changed'}}
        if scenario=='write_failure' and method=='PUT':raise gh.GitHubError('test outage')
        return original(host,path,method,token,body)
    monkeypatch.setattr(gh,'request',altered)
    response=client.post(f'/repository-patches/{pid}/pull-request',json={'accepted':True,'mfa_code':'123456'})
    assert response.status_code==(409 if scenario=='base_changed' else 502)
    with Session() as db:
        p=db.get(RepositoryPatch,pid)
        assert p.pull_number is None
        assert p.status==('review_required' if scenario=='base_changed' else 'publication_unverified')
    outsider=TestClient(app);signup(outsider,mail,'outside@example.test')
    assert outsider.get(f'/organizations/{org}/repository-patches').status_code==403
    assert outsider.post(f'/repository-patches/{pid}/refresh').status_code==403

def test_pr_merge_deployment_record_full_retest_lifecycle(client,mail,monkeypatch,github):
    from test_monitoring_regression import applied,approve,age_jobs
    from test_assessment import GOOD
    from aegis import worker
    from aegis.models import Job,Authorization
    from test_mfa import enroll
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    _,codes,_=enroll(client,monkeypatch) # real MFA enrollment and recovery verification, no factor bypass
    result=client.post(f'/repository-patches/{pid}/pull-request',json={'accepted':True,'mfa_code':codes[0]})
    assert result.status_code==200,result.text
    assert client.post(f'/repository-patches/{pid}/refresh').json()['status']=='merged_awaiting_deployment'
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409
    tid=applied(client,rid);age_jobs()
    with Session() as db:
        auth=db.scalar(select(Authorization).join(Job,Job.authorization_id==Authorization.id)).id
    job=approve(client,tid,auth)
    monkeypatch.setattr(worker,'fetch',lambda origin:GOOD);worker.assess(job)
    retest=client.get(f'/remediations/{rid}/retests').json()[0]
    assert retest['status']=='verified_original'
    assert 'header.nosniff' in retest['comparison']['resolved']
    assert client.get(f'/assessments/{job}/report').content.startswith(b'%PDF')
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==200

def test_missing_key_returns_controlled_error_and_pause_blocks_writes(client,mail,monkeypatch,github):
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    assert client.post('/admin/repository-control',json={'accepted':True}).json()['paused'] is True
    assert client.post(f'/repository-patches/{pid}/pull-request',json={'accepted':True,'mfa_code':'123456'}).status_code==409
    monkeypatch.delenv('GITHUB_TOKEN_KEY')
    response=client.get(f'/organizations/{org}/repository-patches')
    assert response.status_code==503
    assert 'fixture-private-token' not in response.text

def test_publication_control_read_is_staff_only(client,mail,github):
    signup(client,mail)
    assert client.get('/admin/repository-control').status_code==403
    from test_intelligence import as_admin
    as_admin(client)
    assert client.get('/admin/repository-control').json()=={'paused':False}
    assert client.post('/admin/repository-control',json={'accepted':True}).status_code==200
    assert client.get('/admin/repository-control').json()=={'paused':True}


@pytest.mark.parametrize('change',['evidence','status','unversioned'])
def test_publication_requires_the_exact_reviewed_finding_snapshot(client,mail,monkeypatch,github,change):
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    with Session() as db:
        if change=='unversioned':
            patch=db.get(RepositoryPatch,pid)
            patch.test_evidence={k:v for k,v in patch.test_evidence.items() if k!='finding_snapshot'}
        else:
            finding=db.get(Finding,db.get(Remediation,rid).finding_id)
            setattr(finding,change,'resolved' if change=='status' else 'New contradictory evidence')
        db.commit()
    github.clear()
    response=client.post(f'/repository-patches/{pid}/pull-request',json={'accepted':True,'mfa_code':'123456'})
    assert response.status_code==409
    assert 'fresh proposal' in response.json()['detail']
    assert github==[]


@pytest.mark.parametrize('invalid_backup',['missing','wrong_digest','invalid_ciphertext'])
def test_publication_rechecks_encrypted_restore_before_any_repository_write(
    client,mail,monkeypatch,github,invalid_backup
):
    from aegis.models import PatchBackup
    org,rid,cid,pid=patch_setup(client,mail,monkeypatch,github)
    with Session() as db:
        c=db.get(GitHubConnection,cid)
        db.add(MfaState(user_id=c.user_id,secret='fixture',enrollment_session='fixture-session',
                        enabled=True,expires=time.time()+300,last_counter=-1))
        backup=db.scalar(select(PatchBackup).where(PatchBackup.patch_id==pid))
        assert backup is not None
        if invalid_backup=='missing':
            db.delete(backup)
        elif invalid_backup=='wrong_digest':
            backup.sha256='0'*64
            patch=db.get(RepositoryPatch,pid)
            patch.test_evidence={**patch.test_evidence,'backup_sha256':backup.sha256}
        else:
            backup.encrypted_content='not-a-valid-encrypted-backup'
        db.commit()
    monkeypatch.setattr('aegis.mfa.enforce',lambda *args:None)
    github.clear()
    result=client.post(f'/repository-patches/{pid}/pull-request',
                       json={'accepted':True,'mfa_code':'123456'})
    assert result.status_code==409
    assert github==[]
    with Session() as db:
        assert db.get(RepositoryPatch,pid).status=='review_required'
