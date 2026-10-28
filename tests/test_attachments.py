from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import User
from conftest import signup

def create(client,org):
    return client.post(f'/organizations/{org}/support',json={'subject':'Evidence review','body':'Review this bounded evidence.'}).json()['id']

def test_attachment_roundtrip_tenant_and_private(client,mail):
    org=signup(client,mail);tid=create(client,org);base=f'/files/support/{tid}'
    data={'filename':'evidence.txt','content':'Observed header absent.\nمرحبا'}
    r=client.post(base,json=data);assert r.status_code==201;aid=r.json()['id']
    got=client.get(f'{base}/{aid}');assert got.content==data['content'].encode()
    assert got.headers['content-disposition']=='attachment; filename="evidence.txt"'
    assert got.headers['cache-control']=='no-store'
    outsider=TestClient(app);signup(outsider,mail,'other@example.test')
    for url in (base,f'{base}/{aid}'):
        assert outsider.get(url).status_code==403
    assert outsider.delete(f'{base}/{aid}').status_code==403
    assert client.post(base,json={**data,'internal':True}).status_code==403
    with Session() as db:db.scalar(select(User).where(User.email=='other@example.test')).superadmin=True;db.commit()
    staff=f'/files/staff-support/{tid}'
    private=outsider.post(staff,json={**data,'internal':True});assert private.status_code==201
    private_id=private.json()['id']
    assert len(client.get(base).json())==1
    assert client.get(f'{base}/{private_id}').status_code==404
    assert len(outsider.get(staff).json())==2
    assert client.get(staff).status_code==403
    assert client.delete(f'{base}/{aid}').status_code==200
    assert client.get(f'{base}/{aid}').status_code==404

def test_attachment_validation_quota_and_roles(client,mail):
    org=signup(client,mail);tid=create(client,org);base=f'/files/support/{tid}'
    for filename,content,status in [('file.exe','text',422),('../file.txt','text',422),('file.txt','x\x00',422),('file.txt','é'*140000,413)]:
        assert client.post(base,json={'filename':filename,'content':content}).status_code==status
    viewer=TestClient(app);signup(viewer,mail,'viewer@example.test')
    client.post(f'/organizations/{org}/members',json={'email':'viewer@example.test','role':'viewer'})
    data={'filename':'evidence.txt','content':'No secrets.'}
    assert viewer.post(base,json=data).status_code==403
    aid=client.post(base,json=data).json()['id']
    assert viewer.get(f'{base}/{aid}').status_code==200
    assert viewer.delete(f'{base}/{aid}').status_code==403
    client.patch(f'/support/{tid}',json={'status':'closed'})
    assert client.post(base,json=data).status_code==409
    client.patch(f'/support/{tid}',json={'status':'open'})
    for _ in range(19):assert client.post(base,json=data).status_code==201
    assert client.post(base,json=data).status_code==409

def test_body_limit_before_json_parsing(client):
    assert client.post('/files/support/unknown',content=b'x'*(2*1024*1024+1),headers={'content-type':'application/json'}).status_code==413

def test_remediation_private_files_and_parent_binding(client,mail,monkeypatch):
    from test_assessment import authorized,launch,BAD
    from aegis import worker
    org,asset,authorization=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda _:BAD)
    worker.assess(launch(client,asset,authorization))
    finding=client.get(f'/organizations/{org}/findings').json()[0]['id']
    rid=client.post('/remediations',json={'finding_id':finding}).json()['id']
    base=f'/files/remediation/{rid}'
    aid=client.post(base,json={'filename':'plan.md','content':'Review configuration in staging.','internal':True}).json()['id']
    analyst=TestClient(app);signup(analyst,mail,'analyst@example.test')
    client.post(f'/organizations/{org}/members',json={'email':'analyst@example.test','role':'analyst'})
    assert analyst.get(base).json()==[]
    assert analyst.get(f'{base}/{aid}').status_code==404
    assert analyst.post(base,json={'filename':'note.txt','content':'Private','internal':True}).status_code==403
    tid=create(client,org)
    assert client.get(f'/files/support/{tid}/{aid}').status_code==404
    assert client.get(f'{base}/{aid}').status_code==200

