import time
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import LoginSession, User, Membership
from aegis.billing import DisabledPaymentProvider
from conftest import signup
import pytest

def test_registration_login_logout(client, mail):
    org = signup(client, mail)
    me = client.get('/auth/me').json()
    assert me['organizations'][0]['id'] == org
    assert me['verified'] is True
    assert 'httponly' in client.post('/auth/login', json={'email':'owner@example.test','password':'Long-password123!'}).headers['set-cookie'].lower()
    # Refresh CSRF after session rotation.
    client.headers['x-csrf-token'] = client.get('/auth/me').json()['csrf']
    assert client.post('/auth/logout').status_code == 200
    assert client.get('/auth/me').status_code == 401

def test_bad_registration_and_login(client, mail):
    assert client.post('/auth/register', json={'email':'bad','password':'short'}).status_code == 422
    signup(client, mail)
    assert client.post('/auth/login', json={'email':'owner@example.test','password':'wrong-password!'}).status_code == 401
    assert client.post('/auth/register', json={'email':'owner@example.test','password':'Long-password123!'}).status_code == 409

def test_csrf_origin_and_expiration(client, mail):
    signup(client, mail)
    token = client.headers.pop('x-csrf-token')
    assert client.post('/organizations', json={'name':'Blocked'}).status_code == 403
    client.headers['x-csrf-token'] = token
    assert client.post('/organizations', json={'name':'Blocked'}, headers={'origin':'https://evil.test'}).status_code == 403
    with Session() as db:
        for s in db.scalars(select(LoginSession)):
            s.expires = time.time()-1
        db.commit()
    assert client.get('/auth/me').status_code == 401

def test_tenant_and_role_isolation(client, mail):
    org = signup(client, mail)
    other = TestClient(app)
    signup(other, mail, 'viewer@example.test')
    assert other.get(f'/organizations/{org}/members').status_code == 403
    assert client.post(f'/organizations/{org}/members', json={'email':'viewer@example.test','role':'viewer'}).status_code == 200
    assert other.get(f'/organizations/{org}/members').status_code == 200
    assert other.post(f'/organizations/{org}/members', json={'email':'owner@example.test','role':'admin'}).status_code == 403

def test_reset_revokes_sessions_and_token_reuse(client, mail):
    signup(client, mail)
    client.post('/auth/reset-request', json={'email':'owner@example.test'})
    payload = {'token':mail[-1][1], 'password':'New-long-password!'}
    assert client.post('/auth/reset', json=payload).status_code == 200
    assert client.get('/auth/me').status_code == 401
    assert client.post('/auth/reset', json=payload).status_code == 400

def test_unverified_and_deactivation(client, mail):
    client.post('/auth/register',json={'email':'x@example.test','password':'Long-password123!'})
    result = client.post('/auth/login',json={'email':'x@example.test','password':'Long-password123!'})
    client.headers['x-csrf-token'] = result.json()['csrf']
    assert client.post('/organizations',json={'name':'Not yet'}).status_code == 403
    assert client.post('/auth/deactivate').status_code == 409
    assert client.post('/auth/account/deactivate',json={'current_password':'Long-password123!','confirm_deactivation':True}).status_code == 200
    assert client.get('/auth/me').status_code == 401

def test_payments_disabled(client):
    assert client.get('/health').json()['payments_enabled'] is False
    with pytest.raises(RuntimeError):
        DisabledPaymentProvider().create_checkout(None)
