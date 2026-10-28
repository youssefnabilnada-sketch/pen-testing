import os
import tempfile
integration_url=os.getenv('AEGIS_ISOLATED_TEST_DATABASE_URL')
if integration_url:
    from sqlalchemy.engine import make_url
    parsed=make_url(integration_url)
    if parsed.get_backend_name()!='postgresql' or parsed.host not in ('localhost','127.0.0.1') or parsed.database!='aegis_ci':
        raise RuntimeError('Integration tests require an isolated loopback PostgreSQL database named aegis_ci.')
    os.environ['DATABASE_URL']=integration_url
else:
    os.environ['DATABASE_URL'] = 'sqlite:///'+tempfile.mktemp(suffix='.db')
os.environ['TESTING'] = '1'
os.environ['COOKIE_SECURE'] = 'false'
import pytest
from fastapi.testclient import TestClient
from aegis.db import Base, engine, Session
from aegis.main import app
from aegis import main

@pytest.fixture(autouse=True)
def clean():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

@pytest.fixture
def mail(monkeypatch):
    sent = []
    monkeypatch.setattr(main, 'send_token', lambda email, token, purpose: sent.append((email, token, purpose)))
    return sent

@pytest.fixture
def client(mail):
    return TestClient(app)

def signup(client, mail, email='owner@example.test'):
    assert client.post('/auth/register', json={'email':email, 'password':'Long-password123!'}).status_code == 201
    assert client.post('/auth/verify', json={'token':mail[-1][1]}).status_code == 200
    result = client.post('/auth/login', json={'email':email, 'password':'Long-password123!'})
    assert result.status_code == 200
    client.headers['x-csrf-token'] = result.json()['csrf']
    org = client.post('/organizations', json={'name':'Example organization'}).json()['id']
    return org
