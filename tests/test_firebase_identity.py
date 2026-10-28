import time
from conftest import signup
from aegis import firebase_identity as fb
from aegis.db import Session
from aegis.models import Asset
from sqlalchemy import select
TOKEN='controlled-test-token-only'
def configured(monkeypatch):
    monkeypatch.setenv('FIREBASE_AUTH_ENABLED','true')
    monkeypatch.setenv('FIREBASE_PROJECT_ID','test-project')
    claims={'aud':'test-project','iss':'https://securetoken.google.com/test-project','sub':'test-subject','email_verified':True,'auth_time':time.time()}
    monkeypatch.setattr(fb,'sdk_verify',lambda *args:claims)
    return claims

def test_disabled_fails_closed(client,mail):
    signup(client,mail)
    assert client.post('/auth/firebase/login',json={'id_token':TOKEN}).status_code==503

def test_explicit_link_login_unlink(client,mail,monkeypatch):
    signup(client,mail);configured(monkeypatch)
    assert client.post('/auth/firebase/login',json={'id_token':TOKEN}).status_code==401
    data={'id_token':TOKEN,'current_password':'Long-password123!'}
    assert client.post('/auth/firebase/link',json={**data,'current_password':'wrong-password123'}).status_code==401
    assert client.post('/auth/firebase/link',json=data).status_code==200
    client.post('/auth/logout')
    result=client.post('/auth/firebase/login',json={'id_token':TOKEN})
    assert result.status_code==200
    client.headers['x-csrf-token']=result.json()['csrf']
    assert client.get('/auth/me').json()['superadmin'] is False
    with Session() as db:
        assert db.scalar(select(Asset)) is None
    assert client.request('DELETE','/auth/firebase/link',json=data).status_code==200
    assert client.get('/auth/me').status_code==401
    assert client.post('/auth/firebase/login',json={'id_token':TOKEN}).status_code==401

def test_untrusted_claims_and_emulator(client,mail,monkeypatch):
    signup(client,mail)
    for key,value in [('aud','other'),('email_verified',False),('auth_time',0),('sub',''),('iss','evil')]:
        claims=configured(monkeypatch);claims[key]=value
        assert client.post('/auth/firebase/login',json={'id_token':TOKEN}).status_code==401
    configured(monkeypatch)
    monkeypatch.setenv('FIREBASE_AUTH_EMULATOR_HOST','localhost:9099')
    assert client.post('/auth/firebase/login',json={'id_token':TOKEN}).status_code==503

def test_explicit_registration_no_implicit_grants(client,mail,monkeypatch):
    from aegis.models import Membership,User,FirebaseIdentity
    claims=configured(monkeypatch);claims['email']='new@example.test'
    payload={'id_token':TOKEN,'recovery_password':'Recovery-password123!'}
    result=client.post('/auth/firebase/register',json=payload)
    assert result.status_code==201,result.text
    assert client.get('/auth/me').status_code==401
    login=client.post('/auth/firebase/login',json={'id_token':TOKEN})
    assert login.status_code==200
    me=client.get('/auth/me').json()
    assert me['organizations']==[] and not me['superadmin']
    assert client.post('/auth/firebase/register',json=payload).status_code==409
    with Session() as db:
        assert len(db.scalars(select(User)).all())==1
        assert db.scalar(select(Membership)) is None

def test_email_collision_does_not_link(client,mail,monkeypatch):
    signup(client,mail);claims=configured(monkeypatch);claims['email']='owner@example.test'
    assert client.post('/auth/firebase/register',json={'id_token':TOKEN,'recovery_password':'Recovery-password123!'}).status_code==409
    assert client.get('/auth/firebase/status').json()['linked'] is False
    client.headers['x-csrf-token']='bad'
    assert client.post('/auth/firebase/link',json={'id_token':TOKEN,'current_password':'Long-password123!'}).status_code==403

def test_config_no_secrets_and_provider_failure(client,mail,monkeypatch):
    from fastapi import HTTPException
    assert client.get('/auth/firebase/config').json()=={'enabled':False}
    configured(monkeypatch)
    monkeypatch.setenv('FIREBASE_WEB_API_KEY','public-web-key')
    monkeypatch.setenv('FIREBASE_WEB_APP_ID','public-app-id')
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS','must-not-be-returned')
    r=client.get('/auth/firebase/config')
    assert r.json()['enabled'] is True and 'must-not-be-returned' not in r.text
    def fail(*args):raise HTTPException(401,'Firebase identity could not be verified.')
    monkeypatch.setattr(fb,'sdk_verify',fail)
    assert client.post('/auth/firebase/login',json={'id_token':TOKEN}).status_code==401

def test_admin_sdk_enforces_revocation_and_hides_provider_errors(monkeypatch):
    import pytest
    from firebase_admin import auth
    from fastapi import HTTPException
    sentinel=object();seen={}
    monkeypatch.setattr(fb,'firebase_app',lambda project:sentinel)
    def verify(token,**kwargs):
        seen.update(kwargs)
        return {'sub':'verified'}
    monkeypatch.setattr(auth,'verify_id_token',verify)
    assert fb.sdk_verify(TOKEN,'test-project')['sub']=='verified'
    assert seen=={'app':sentinel,'check_revoked':True}
    def revoked(*args,**kwargs):raise ValueError('sensitive-provider-detail')
    monkeypatch.setattr(auth,'verify_id_token',revoked)
    with pytest.raises(HTTPException) as err:fb.sdk_verify(TOKEN,'test-project')
    assert err.value.status_code==401 and 'sensitive-provider-detail' not in err.value.detail
