import time
from types import SimpleNamespace
import pyotp
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis import mfa,firebase_identity as fb
from aegis.db import Session
from aegis.models import MfaState,RecoveryCode,User,FirebaseIdentity
from conftest import signup
PASSWORD='Long-password123!'
def enroll(client,monkeypatch):
    monkeypatch.setenv('MFA_ENCRYPTION_KEY',Fernet.generate_key().decode())
    now=time.time();monkeypatch.setattr(mfa,'time',SimpleNamespace(time=lambda:now))
    r=client.post('/auth/mfa/setup',json={'current_password':PASSWORD})
    assert r.status_code==200
    secret=r.json()['secret'];code=pyotp.TOTP(secret).at(mfa.time.time())
    confirmed=client.post('/auth/mfa/confirm',json={'code':code})
    assert confirmed.status_code==200
    return secret,confirmed.json()['recovery_codes'],now

def test_enrollment_recovery_and_replay(client,mail,monkeypatch):
    signup(client,mail)
    other=TestClient(app);other.post('/auth/login',json={'email':'owner@example.test','password':PASSWORD})
    secret,codes,_=enroll(client,monkeypatch)
    assert other.get('/auth/me').status_code==401
    with Session() as db:
        state=db.scalar(select(MfaState));assert secret not in state.secret
        assert len(db.scalars(select(RecoveryCode)).all())==10
        assert not any(r.digest in codes for r in db.scalars(select(RecoveryCode)))
    client.post('/auth/logout')
    login={'email':'owner@example.test','password':PASSWORD}
    assert client.post('/auth/login',json=login).status_code==401
    assert client.post('/auth/login',json={**login,'mfa_code':pyotp.TOTP(secret).at(mfa.time.time())}).status_code==401
    r=client.post('/auth/login',json={**login,'mfa_code':codes[0]});assert r.status_code==200
    client.headers['x-csrf-token']=r.json()['csrf']
    client.post('/auth/logout')
    assert client.post('/auth/login',json={**login,'mfa_code':codes[0]}).status_code==401
    r=client.post('/auth/login',json={**login,'mfa_code':codes[1]});client.headers['x-csrf-token']=r.json()['csrf']
    assert client.post('/auth/mfa/disable',json={'current_password':PASSWORD,'code':codes[2]}).status_code==200
    assert client.get('/auth/me').status_code==401
    assert client.post('/auth/login',json=login).status_code==200

def test_pending_enrollment_bound_to_session_and_expiry(client,mail,monkeypatch):
    signup(client,mail);monkeypatch.setenv('MFA_ENCRYPTION_KEY',Fernet.generate_key().decode())
    assert client.post('/auth/mfa/setup',json={'current_password':'incorrect-password'}).status_code==401
    s=client.post('/auth/mfa/setup',json={'current_password':PASSWORD}).json()['secret']
    other=TestClient(app);r=other.post('/auth/login',json={'email':'owner@example.test','password':PASSWORD});other.headers['x-csrf-token']=r.json()['csrf']
    assert other.post('/auth/mfa/confirm',json={'code':pyotp.TOTP(s).at(mfa.time.time())}).status_code==409
    with Session() as db:db.scalar(select(MfaState)).expires=0;db.commit()
    assert client.post('/auth/mfa/confirm',json={'code':pyotp.TOTP(s).at(mfa.time.time())}).status_code==409
    monkeypatch.delenv('MFA_ENCRYPTION_KEY')
    assert client.post('/auth/mfa/setup',json={'current_password':PASSWORD}).status_code==503

def test_firebase_and_reset_cannot_bypass_factor(client,mail,monkeypatch):
    signup(client,mail);_,codes,_=enroll(client,monkeypatch)
    with Session() as db:
        uid=db.scalar(select(User)).id
        db.add(FirebaseIdentity(user_id=uid,project='fixture',subject='subject'));db.commit()
    monkeypatch.setattr(fb,'verified_identity',lambda token:('fixture',{'sub':'subject'}))
    token={'id_token':'controlled-token-for-fixture'}
    assert client.post('/auth/firebase/login',json=token).status_code==401
    assert client.post('/auth/firebase/login',json={**token,'mfa_code':codes[0]}).status_code==200
    client.post('/auth/reset-request',json={'email':'owner@example.test'})
    assert client.post('/auth/reset',json={'token':mail[-1][1],'password':'Replacement-password123!'}).status_code==200
    assert client.post('/auth/login',json={'email':'owner@example.test','password':'Replacement-password123!'}).status_code==401

def test_totp_new_counter_and_missing_key_fail_closed(client,mail,monkeypatch):
    signup(client,mail);secret,codes,_=enroll(client,monkeypatch)
    with Session() as db:
        state=db.scalar(select(MfaState));state.last_counter-=1;db.commit()
    payload={'email':'owner@example.test','password':PASSWORD,'mfa_code':pyotp.TOTP(secret).at(mfa.time.time())}
    assert client.post('/auth/login',json=payload).status_code==200
    assert client.post('/auth/login',json=payload).status_code==401
    monkeypatch.delenv('MFA_ENCRYPTION_KEY')
    assert client.post('/auth/login',json=payload).status_code==503
    # Offline backup codes can recover when a seed key is unavailable; still requires password.
    assert client.post('/auth/login',json={**payload,'mfa_code':codes[0]}).status_code==200

def test_identity_link_changes_require_factor_when_enabled(client,mail,monkeypatch):
    signup(client,mail);_,codes,_=enroll(client,monkeypatch)
    monkeypatch.setattr(fb,'verified_identity',lambda token:('fixture',{'sub':'subject'}))
    data={'id_token':'controlled-token-for-fixture','current_password':PASSWORD}
    assert client.post('/auth/firebase/link',json=data).status_code==401
    assert client.post('/auth/firebase/link',json={**data,'mfa_code':codes[0]}).status_code==200
    assert client.request('DELETE','/auth/firebase/link',json={'current_password':PASSWORD}).status_code==401
    assert client.request('DELETE','/auth/firebase/link',json={'current_password':PASSWORD,'mfa_code':codes[1]}).status_code==200
    assert client.get('/auth/me').status_code==401
