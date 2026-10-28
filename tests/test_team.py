import time
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import TeamInvitation,Membership,User
from aegis import team
from conftest import signup

def test_invite_accept_roles_and_immediate_removal(client,mail,monkeypatch):
    org=signup(client,mail);sent=[]
    monkeypatch.setattr(team,'send_invitation',lambda *args:sent.append(args))
    other=TestClient(app);signup(other,mail,'invitee@example.test')
    uid=other.get('/auth/me').json()['id']
    invitation=client.post(f'/organizations/{org}/invitations',json={'email':'invitee@example.test','role':'viewer'})
    assert invitation.status_code==201 and len(sent)==1
    iid=invitation.json()['id']
    assert other.get(f'/organizations/{org}/assets').status_code==403
    assert other.get('/invitations/incoming').json()[0]['id']==iid
    assert other.post(f'/invitations/{iid}/accept').status_code==200
    assert other.post(f'/invitations/{iid}/accept').status_code==409
    assert other.get(f'/organizations/{org}/assets').status_code==200
    assert other.post(f'/organizations/{org}/invitations',json={'email':'third@example.test','role':'admin'}).status_code==403
    assert client.patch(f'/organizations/{org}/members/{uid}',json={'role':'analyst'}).status_code==200
    assert client.delete(f'/organizations/{org}/members/{uid}').status_code==200
    assert other.get(f'/organizations/{org}/assets').status_code==403
    with Session() as db:assert db.get(TeamInvitation,iid).status=='accepted'

def test_recipient_expiry_revocation_and_duplicates(client,mail,monkeypatch):
    org=signup(client,mail);monkeypatch.setattr(team,'send_invitation',lambda *args:None)
    payload={'email':'other@example.test','role':'viewer'}
    iid=client.post(f'/organizations/{org}/invitations',json=payload).json()['id']
    assert client.post(f'/organizations/{org}/invitations',json=payload).status_code==409
    assert client.post(f'/invitations/{iid}/accept').status_code==404
    outsider=TestClient(app);their=signup(outsider,mail,'other@example.test')
    assert outsider.get(f'/organizations/{org}/invitations').status_code==403
    assert outsider.delete(f'/organizations/{their}/invitations/{iid}').status_code==404
    assert client.delete(f'/organizations/{org}/invitations/{iid}').status_code==200
    assert outsider.post(f'/invitations/{iid}/accept').status_code==409
    iid=client.post(f'/organizations/{org}/invitations',json=payload).json()['id']
    with Session() as db:db.get(TeamInvitation,iid).expires=time.time()-1;db.commit()
    assert outsider.post(f'/invitations/{iid}/accept').status_code==409
    assert outsider.get('/invitations/incoming').json()==[]

def test_mail_failure_and_owner_protection(client,mail,monkeypatch):
    org=signup(client,mail);uid=client.get('/auth/me').json()['id']
    def fail(*args):raise OSError('provider-secret')
    monkeypatch.setattr(team,'send_invitation',fail)
    response=client.post(f'/organizations/{org}/invitations',json={'email':'new@example.test','role':'viewer'})
    assert response.status_code==503 and 'provider-secret' not in response.text
    with Session() as db:assert db.scalar(select(TeamInvitation)) is None
    assert client.patch(f'/organizations/{org}/members/{uid}',json={'role':'viewer'}).status_code==403
    assert client.delete(f'/organizations/{org}/members/{uid}').status_code==403

def test_demoted_inviter_cannot_grant_stale_access(client,mail,monkeypatch):
    org=signup(client,mail);monkeypatch.setattr(team,'send_invitation',lambda *args:None)
    staff=TestClient(app);signup(staff,mail,'admin@example.test')
    uid=staff.get('/auth/me').json()['id']
    assert client.post(f'/organizations/{org}/members',json={'email':'admin@example.test','role':'admin'}).status_code==200
    assert staff.post(f'/organizations/{org}/invitations',json={'email':'third@example.test','role':'admin'}).status_code==403
    iid=staff.post(f'/organizations/{org}/invitations',json={'email':'third@example.test','role':'viewer'}).json()['id']
    third=TestClient(app);signup(third,mail,'third@example.test')
    with Session() as db:
        db.scalar(select(Membership).where(Membership.user_id==uid,Membership.org_id==org)).role='viewer';db.commit()
    assert third.post(f'/invitations/{iid}/accept').status_code==403
    with Session() as db:db.scalar(select(User).where(User.email=='third@example.test')).verified=False;db.commit()
    assert third.get('/invitations/incoming').status_code==403
