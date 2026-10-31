import base64
import time
import tomllib
import pytest
from aegis.fastfix_adapters import propose_netlify_nosniff,patch_file
from aegis import github_client as gh
from aegis.db import Session
from aegis.models import RepositoryPatch,Remediation,Finding,MfaState,GitHubConnection
from test_repositories import github,patch_setup  # noqa: F401


def test_preserves_source_comments_and_build_without_execution():
    source='# preserve me\n[build]\ncommand="do not execute"\npublish="dist"\n'
    result=propose_netlify_nosniff(source)
    assert result.startswith(source)
    assert tomllib.loads(result)['build']==tomllib.loads(source)['build']
    assert tomllib.loads(result)['headers'][0]['values']['X-Content-Type-Options']=='nosniff'


@pytest.mark.parametrize('source',[
    'headers = {}',
    '[[headers]]\nfor="/*"',
    '[[headers]]\nfor="/*"\n[headers.values]\nx-CONTENT-type-OPTIONS="unsafe"',
    'a=1\na=2',
    '#'+('x'*65535),
    '\x00',
], ids=['invalid-table','missing-values','existing-policy','duplicate-key','size-limit','null-byte'])
def test_rejects_ambiguous_invalid_or_oversized_configuration(source):
    with pytest.raises(ValueError):propose_netlify_nosniff(source)


def test_netlify_proposal_backup_and_mfa_boundary(client,mail,monkeypatch,github):
    org,rid,cid,_=patch_setup(client,mail,monkeypatch,github)
    original=gh.request
    source=b'# preserved\n[build]\npublish="dist"\n'
    def request(host,path,method='GET',token=None,body=None):
        if '/contents/netlify.toml?' in path:
            return {'type':'file','encoding':'base64','size':len(source),'sha':'b'*40,'content':base64.b64encode(source).decode()}
        return original(host,path,method,token,body)
    monkeypatch.setattr(gh,'request',request)
    data={'connection_id':cid,'repository':'owned/site','remediation_id':rid,'accepted':True,'adapter':'netlify'}
    result=client.post('/repository-patches',json=data)
    assert result.status_code==200,result.text
    p=result.json();assert 'b/netlify.toml' in p['diff']
    assert p['tests']['adapter']=='netlify' and p['tests']['configuration_valid']
    assert 'netlify.toml only' in p['tests']['backup_scope']
    rollback=client.post('/repository-patches/'+p['id']+'/rollback-preview')
    assert rollback.status_code==200 and rollback.json()['restore_verified']
    assert 'restored/netlify.toml' in rollback.json()['diff']
    assert client.post('/repository-patches/'+p['id']+'/pull-request',json={'accepted':True,'mfa_code':'123456'}).status_code==403
    assert client.post('/repository-patches',json={**data,'adapter':'../../file'}).status_code==422
    with Session() as db:
        patch=db.get(RepositoryPatch,p['id']);assert patch_file(patch)=='netlify.toml'
        remediation=db.get(Remediation,rid)
        finding=db.get(Finding,remediation.finding_id)
        assert finding.status!='resolved'

    with Session() as db:
        c=db.get(GitHubConnection,cid)
        db.add(MfaState(user_id=c.user_id,secret='fixture',enrollment_session='fixture-session',enabled=True,expires=time.time()+300,last_counter=-1));db.commit()
    monkeypatch.setattr('aegis.mfa.enforce',lambda *args:None)
    published=client.post('/repository-patches/'+p['id']+'/pull-request',json={'accepted':True,'mfa_code':'123456'})
    assert published.status_code==200,published.text
    writes=[(path,method,body) for path,method,body in github if method in ('POST','PUT')]
    assert any(path.endswith('/contents/netlify.toml') and method=='PUT' for path,method,body in writes)
    assert all(not path.endswith('/contents/vercel.json') for path,method,body in writes)
    assert writes[-1][2]['draft'] is True


@pytest.mark.parametrize('bad',[None,[],{'type':'file','encoding':'base64','size':'13'}, {'type':'file','encoding':'base64','size':10,'content':'!!!','sha':'b'*40}])
def test_invalid_provider_file_never_creates_a_proposal(client,mail,monkeypatch,github,bad):
    org,rid,cid,_=patch_setup(client,mail,monkeypatch,github)
    original=gh.request
    def request(host,path,method='GET',token=None,body=None):
        if '/contents/netlify.toml?' in path:return bad
        return original(host,path,method,token,body)
    monkeypatch.setattr(gh,'request',request)
    result=client.post('/repository-patches',json={'connection_id':cid,'repository':'owned/site','remediation_id':rid,'accepted':True,'adapter':'netlify'})
    assert result.status_code==409
    assert not any(method in ('POST','PUT') for _,method,_ in github)


@pytest.mark.parametrize('source', [
    '[context.production]\ncommand="build"',
    '[[redirects]]\nfrom="/*"\nto="https://upstream.invalid/:splat"\nstatus=200',
    '[functions]\ndirectory="functions"',
    '[[edge_functions]]\npath="/*"\nfunction="headers"',
    '[[plugins]]\npackage="custom-plugin"',
])
def test_dynamic_or_context_configuration_requires_manual_review(source):
    with pytest.raises(ValueError, match='manual review'):
        propose_netlify_nosniff(source)
