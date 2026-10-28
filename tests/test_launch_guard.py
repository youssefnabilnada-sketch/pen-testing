from fastapi.testclient import TestClient
from aegis.main import app
from aegis import github_client as gh
from aegis.launch_guard import summarize
from conftest import signup
from test_repositories import github,connect

def test_no_checks_or_truncated_evidence_is_never_passed():
    assert summarize({'total_count':0,'check_runs':[]},{'total_count':0,'statuses':[]},[])['ci']!='passed'
    assert summarize({'total_count':2,'check_runs':[{'status':'completed','conclusion':'success'}]},{'total_count':0,'statuses':[]},[])['ci']!='passed'

def test_authorized_review_exact_head_revocation_and_tenant(client,mail,monkeypatch,github):
    org=signup(client,mail);cid,_=connect(client,org);sha='a'*40
    def request(host,path,method='GET',token=None,body=None):
        assert method=='GET'
        if path=='/repos/owned/site':return {'permissions':{'pull':True}}
        if path.endswith('/pulls/1'):return {'head':{'sha':sha,'repo':{'full_name':'owned/site'}},'changed_files':1}
        if '/files?' in path:return [{'filename':'package.json','status':'modified'}]
        if '/check-runs?' in path:return {'total_count':1,'check_runs':[{'name':'tests','head_sha':sha,'status':'completed','conclusion':'success'}]}
        if '/status?' in path:return {'sha':sha,'total_count':0,'statuses':[]}
        raise AssertionError(path)
    monkeypatch.setattr(gh,'request',request)
    data={'connection_id':cid,'repository':'owned/site','pull_request':1,'accepted':True}
    assert client.post('/launch-reviews',json={**data,'accepted':False}).status_code==403
    r=client.post('/launch-reviews',json=data);assert r.status_code==200,r.text
    assert r.json()['result']['ci']=='passed' and r.json()['result']['changed_files'][0]['review_required']
    assert r.json()['result']['staging']=='not_run'
    other=TestClient(app);signup(other,mail,'release-other@example.test')
    assert other.get(f'/organizations/{org}/launch-reviews').status_code==403
    assert other.post('/launch-reviews',json=data).status_code==403
    client.delete(f'/github/connections/{cid}')
    assert client.post('/launch-reviews',json=data).status_code==409


import pytest
from fastapi import HTTPException

@pytest.mark.parametrize('checks,statuses,files',[
    (None,{},[]),
    ({'total_count':True,'check_runs':[]},{'total_count':0,'statuses':[]},[]),
    ({'total_count':1,'check_runs':[None]},{'total_count':0,'statuses':[]},[]),
    ({'total_count':0,'check_runs':[]},{'total_count':1,'statuses':['success']},[]),
    ({'total_count':0,'check_runs':[]},{'total_count':0,'statuses':[]},[None]),
    ({'total_count':0,'check_runs':[]},{'total_count':0,'statuses':[]},[{'filename':42}]),
])
def test_malformed_provider_payload_fails_closed(checks,statuses,files):
    with pytest.raises(HTTPException) as e:summarize(checks,statuses,files)
    assert e.value.status_code==502


def test_role_downgrade_during_provider_fetch_prevents_review(client,mail,monkeypatch,github):
    from sqlalchemy import select
    from aegis.db import Session
    from aegis.models import Membership,LaunchReview
    org=signup(client,mail);cid,_=connect(client,org);sha='b'*40;pulls=[]
    def request(host,path,method='GET',token=None,body=None):
        if path=='/repos/owned/site':return {'permissions':{'pull':True}}
        if path.endswith('/pulls/1'):
            pulls.append(path)
            if len(pulls)==2:
                with Session() as db:
                    db.scalar(select(Membership).where(Membership.org_id==org)).role='viewer';db.commit()
            return {'head':{'sha':sha,'repo':{'full_name':'owned/site'}},'changed_files':0}
        if '/files?' in path:return []
        if '/check-runs?' in path:return {'total_count':0,'check_runs':[]}
        if '/status?' in path:return {'sha':sha,'total_count':0,'statuses':[]}
        raise AssertionError(path)
    monkeypatch.setattr(gh,'request',request)
    r=client.post('/launch-reviews',json={'connection_id':cid,'repository':'owned/site','pull_request':1,'accepted':True})
    assert r.status_code==403
    with Session() as db:assert db.scalar(select(LaunchReview)) is None
