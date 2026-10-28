import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import Challenge
from aegis import safety
from conftest import signup

def setup(client, mail, monkeypatch):
    org = signup(client, mail)
    monkeypatch.setattr(safety, 'resolve', lambda o: ('example.test',443,'93.184.216.34','https'))
    a = client.post(f'/organizations/{org}/assets', json={'origin':'https://example.test'}).json()['id']
    return a

def test_reuse_recovery_expiry_and_revoke(client, mail, monkeypatch):
    a = setup(client, mail, monkeypatch)
    path = f'/assets/{a}/challenge'
    assert client.get(path).json() is None
    c = client.post(path,json={'method':'file'}).json()
    assert client.post(path,json={'method':'file'}).json() == c
    assert client.get(path).json() == c
    with Session() as db:
        db.get(Challenge,c['id']).expires = time.time()-1
        db.commit()
    newer = client.post(path,json={'method':'file'}).json()
    assert newer['token'] != c['token']
    assert client.post(f'/assets/{a}/revoke').status_code == 200
    assert client.get(path).json() is None
    assert client.post(f'/assets/{a}/verify/{newer["id"]}').status_code == 400

def test_prefilled_github_is_not_ownership_and_is_tenant_scoped(client, mail, monkeypatch):
    a = setup(client, mail, monkeypatch)
    c = client.post(f'/assets/{a}/challenge',json={'method':'file'}).json()
    path = f'/assets/{a}/challenge/{c["id"]}/github'
    result = client.post(path,json={'repository':'owner/site','directory':'public'})
    assert result.status_code == 200
    assert result.json()['url'].startswith('https://github.com/owner/site/new/main?')
    assert 'public%2F.well-known%2Faegis-' in result.json()['url']
    assert client.post(f'/assets/{a}/authorize',json={'accepted':True}).status_code == 403
    for body in [{'repository':'https://evil.test/a'}, {'repository':'a/b','branch':'../x'}, {'repository':'a/b','directory':'../'}]:
        assert client.post(path,json=body).status_code == 422
    other = TestClient(app)
    signup(other,mail,'other@example.test')
    assert other.get(f'/assets/{a}/challenge').status_code == 403
    assert other.post(path,json={'repository':'owner/site'}).status_code == 403

def test_one_click_review_is_idempotent_not_a_fix(client,mail,monkeypatch):
    from test_assessment import authorized,launch,BAD
    from aegis import worker
    from aegis.models import Finding,Remediation
    org,a,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda origin:BAD)
    worker.assess(launch(client,a,auth))
    path=f'/assets/{a}/request-remediation'
    result=client.post(path)
    assert result.status_code==201 and result.json()['applied'] is False
    assert result.json()['count']==6
    assert client.post(path).json()['request_ids']==result.json()['request_ids']
    with Session() as db:
        assert len(db.scalars(select(Remediation)).all())==6
        assert all(f.status=='remediation_requested' for f in db.scalars(select(Finding)))
    other=TestClient(app);signup(other,mail,'outside@example.test')
    assert other.post(path).status_code==403
