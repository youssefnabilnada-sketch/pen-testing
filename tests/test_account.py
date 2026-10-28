from fastapi.testclient import TestClient
from sqlalchemy import select,delete
from aegis.main import app
from aegis.db import Session
from aegis.models import Membership,User,EmailToken
from conftest import signup
PASSWORD='Long-password123!'
def test_profile_password_sessions_and_mfa(client,mail,monkeypatch):
    from test_mfa import enroll
    signup(client,mail)
    assert client.patch('/auth/account',json={'display_name':' Analyst '}).json()=={'display_name':'Analyst'}
    assert client.get('/auth/account').json()['display_name']=='Analyst'
    assert client.patch('/auth/account',json={'display_name':'Other','user_id':'foreign'}).status_code==422
    assert client.patch('/auth/account',json={'display_name':'   '}).status_code==422
    _,codes,_=enroll(client,monkeypatch)
    change={'current_password':PASSWORD,'new_password':'Replacement-password123!'}
    assert client.post('/auth/account/password',json=change).status_code==401
    assert client.post('/auth/account/password',json={**change,'mfa_code':codes[0]}).status_code==200
    assert client.get('/auth/me').status_code==401
    assert client.post('/auth/login',json={'email':'owner@example.test','password':PASSWORD,'mfa_code':codes[1]}).status_code==401
    assert client.post('/auth/login',json={'email':'owner@example.test','password':change['new_password'],'mfa_code':codes[1]}).status_code==200

def test_deactivate_preserves_owner_and_revokes_account(client,mail):
    org=signup(client,mail)
    assert client.post('/auth/deactivate').status_code==409
    data={'current_password':PASSWORD,'confirm_deactivation':True}
    assert client.post('/auth/account/deactivate',json=data).status_code==409
    assert client.post('/auth/account/deactivate',json={**data,'confirm_deactivation':False}).status_code==422
    other=TestClient(app)
    result=other.post('/auth/login',json={'email':'owner@example.test','password':PASSWORD});assert result.status_code==200
    with Session() as db:
        # Fixture represents a non-owner account after an independently completed transfer.
        db.execute(delete(Membership).where(Membership.org_id==org));db.commit()
    client.post('/auth/reset-request',json={'email':'owner@example.test'})
    assert client.post('/auth/account/deactivate',json={**data,'current_password':'incorrect-password'}).status_code==401
    assert client.post('/auth/account/deactivate',json=data).status_code==200
    assert other.get('/auth/me').status_code==401
    assert client.post('/auth/login',json={'email':'owner@example.test','password':PASSWORD}).status_code==401
    with Session() as db:
        assert db.scalar(select(User)).active is False
        assert db.scalar(select(EmailToken)) is None
    assert client.post('/auth/reset',json={'token':mail[-1][1],'password':'Replacement-password123!'}).status_code==400

def test_signout_all_and_admin_deactivation_guard(client,mail):
    signup(client,mail)
    with Session() as db:db.scalar(select(User)).superadmin=True;db.commit()
    assert client.post('/auth/account/deactivate',json={'current_password':PASSWORD,'confirm_deactivation':True}).status_code==409
    assert client.post('/auth/account/sign-out-all',json={'current_password':PASSWORD}).status_code==200
    assert client.get('/auth/me').status_code==401

def test_explicit_ownership_transfer_and_deactivation(client,mail):
    org=signup(client,mail)
    recipient=TestClient(app);signup(recipient,mail,'recipient@example.test')
    uid=recipient.get('/auth/me').json()['id']
    route=f'/organizations/{org}/transfer-ownership'
    data={'current_password':PASSWORD,'target_user_id':uid,'confirm_email':'recipient@example.test','confirm_transfer':True}
    assert client.post(route,json=data).status_code==409
    client.post(f'/organizations/{org}/members',json={'email':'recipient@example.test','role':'admin'})
    assert recipient.post(route,json=data).status_code in (403,422)
    assert client.post(route,json={**data,'confirm_email':'wrong@example.test'}).status_code==422
    assert client.post(route,json={**data,'current_password':'incorrect-password'}).status_code==401
    assert client.post(route,json={**data,'confirm_transfer':False}).status_code==422
    assert client.post(route,json=data).status_code==200
    assert client.post(route,json=data).status_code==403
    with Session() as db:
        owners=db.scalars(select(Membership).where(Membership.org_id==org,Membership.role=='owner')).all()
        assert len(owners)==1 and owners[0].user_id==uid
    assert client.post('/auth/account/deactivate',json={'current_password':PASSWORD,'confirm_deactivation':True}).status_code==200
    assert recipient.get(f'/organizations/{org}/members').status_code==200
