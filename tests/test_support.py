from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import User
from conftest import signup

def test_support_tenant_boundary_and_staff_notes(client,mail):
    org=signup(client,mail)
    response=client.post(f'/organizations/{org}/support',json={'subject':'Report question','body':'Please explain the supported assessment scope.'})
    assert response.status_code==201;tid=response.json()['id']
    outsider=TestClient(app);other=signup(outsider,mail,'other@example.test')
    assert outsider.get(f'/support/{tid}').status_code==403
    assert outsider.post(f'/support/{tid}/messages',json={'body':'wrong tenant'}).status_code==403
    assert outsider.patch(f'/support/{tid}',json={'status':'closed'}).status_code==403
    assert outsider.get('/admin/support').status_code==403
    assert outsider.get(f'/organizations/{other}/support').json()==[]
    with Session() as db:db.scalar(select(User).where(User.email=='other@example.test')).superadmin=True;db.commit()
    assert outsider.post(f'/admin/support/{tid}/messages',json={'body':'Staff-only review note','internal':True}).status_code==200
    assert 'Staff-only' not in client.get(f'/support/{tid}').text
    assert client.get(f'/support/{tid}').json()['status']=='open'
    assert 'Staff-only' in outsider.get(f'/admin/support/{tid}').text
    assert outsider.post(f'/admin/support/{tid}/messages',json={'body':'Only approved safe checks are run.'}).status_code==200
    assert client.get(f'/support/{tid}').json()['status']=='awaiting_customer'
    assert client.patch(f'/support/{tid}',json={'status':'closed'}).status_code==200
    assert client.post(f'/support/{tid}/messages',json={'body':'More information'}).status_code==409
    assert client.patch(f'/support/{tid}',json={'status':'open'}).status_code==200
    assert client.post(f'/support/{tid}/messages',json={'body':'Thanks, please review again.'}).status_code==200

def test_support_viewer_and_validation(client,mail):
    org=signup(client,mail);viewer=TestClient(app);signup(viewer,mail,'viewer@example.test')
    client.post(f'/organizations/{org}/members',json={'email':'viewer@example.test','role':'viewer'})
    assert viewer.post(f'/organizations/{org}/support',json={'subject':'Need help','body':'Test'}).status_code==403
    assert client.post(f'/organizations/{org}/support',json={'subject':'   ','body':'Test'}).status_code==422
    tid=client.post(f'/organizations/{org}/support',json={'subject':'Need help','body':'Test'}).json()['id']
    assert viewer.get(f'/support/{tid}').status_code==200
    assert viewer.post(f'/support/{tid}/messages',json={'body':'Test'}).status_code==403
    assert client.post(f'/support/{tid}/messages',json={'body':'   '}).status_code==422
    assert client.patch(f'/support/{tid}',json={'status':'invented'}).status_code==422
    assert client.get(f'/support/{tid}?offset=-1').status_code==422
    assert len(client.get(f'/support/{tid}').json()['messages'])==1
