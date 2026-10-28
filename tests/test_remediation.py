from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import User
from aegis import worker
from conftest import signup
from test_assessment import authorized, launch, BAD, GOOD

def test_complete_quote_workflow_tenant_messages_no_payment(client,mail,monkeypatch):
    org,a,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda o:BAD)
    jid=launch(client,a,auth);worker.assess(jid)
    finding=client.get(f'/organizations/{org}/findings').json()[0]['id']
    r=client.post('/remediations',json={'finding_id':finding});assert r.status_code==201
    rid=r.json()['id']
    assert client.post('/remediations',json={'finding_id':finding}).status_code==409
    assert client.patch(f'/remediations/{rid}/task',json={'status':'in_progress'}).status_code==409
    quote={'scope':'Review configuration, apply an approved change in staging and retest. No production deployment authorized.','amount_minor':0,'currency':'EGP'}
    assert client.post(f'/admin/remediations/{rid}/quote',json=quote).status_code==403
    staff=TestClient(app);signup(staff,mail,'admin@example.test')
    with Session() as db:
        db.scalar(select(User).where(User.email=='admin@example.test')).superadmin=True;db.commit()
    assert staff.post(f'/admin/remediations/{rid}/quote',json={**quote,'amount_minor':10000}).status_code==422
    assert staff.post(f'/admin/remediations/{rid}/quote',json=quote).status_code==200
    assert client.get(f'/organizations/{org}/remediations').json()[0]['amount_minor'] is None
    assert client.post(f'/remediations/{rid}/decision',json={'accept':True}).status_code==200
    assert 'no payment collected' in client.get(f'/organizations/{org}/remediations').json()[0]['payment_status']
    assert staff.post(f'/admin/remediations/{rid}/quote',json=quote).status_code==409
    assert client.patch(f'/remediations/{rid}/task',json={'status':'in_progress'}).status_code==200
    assert client.post(f'/remediations/{rid}/messages',json={'body':'Approved test-only change; please validate.'}).status_code==200
    assert staff.get(f'/remediations/{rid}/messages').status_code==403
    assert client.patch(f'/remediations/{rid}/task',json={'status':'ready_for_retest'}).status_code==200
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409
    monkeypatch.setattr(worker,'fetch',lambda o:GOOD)
    jid2=launch(client,a,auth);worker.assess(jid2)
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409  # Ad-hoc scan alone no longer satisfies full-retest approval.
    assert client.get('/admin/overview').status_code==403
    overview=staff.get('/admin/overview');assert overview.status_code==200
    assert overview.json()['payments_enabled'] is False
    assert staff.post('/admin/assessment-control',json={'paused':True}).status_code==200
    assert client.post(f'/assets/{a}/assessments',json={'authorization_id':auth}).status_code==503

def test_internal_notes_hidden_from_viewer(client,mail,monkeypatch):
    org,a,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda o:BAD);worker.assess(launch(client,a,auth))
    finding=client.get(f'/organizations/{org}/findings').json()[0]['id']
    rid=client.post('/remediations',json={'finding_id':finding}).json()['id']
    viewer=TestClient(app);signup(viewer,mail,'viewer@example.test')
    client.post(f'/organizations/{org}/members',json={'email':'viewer@example.test','role':'viewer'})
    client.post(f'/remediations/{rid}/messages',json={'body':'Internal review note','internal':True})
    assert viewer.get(f'/remediations/{rid}/messages').json()==[]
    assert viewer.post(f'/remediations/{rid}/messages',json={'body':'blocked'}).status_code==403
    assert viewer.patch(f'/findings/{finding}',json={'status':'resolved'}).status_code==403
    assert client.patch(f'/findings/{finding}',json={'status':'resolved'}).status_code==422
