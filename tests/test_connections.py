import json
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from aegis import connections as c, firebase_identity as fb
from aegis.db import connection_url, Session
from aegis.models import User
from sqlalchemy import select
from conftest import signup

def test_database_components_preserve_password(monkeypatch):
    monkeypatch.delenv('DATABASE_URL',raising=False)
    monkeypatch.setenv('DATABASE_HOST','db')
    monkeypatch.setenv('DATABASE_PASSWORD','punctuation:@/#%$secret')
    url=connection_url()
    assert url.password=='punctuation:@/#%$secret' and url.host=='db'
    assert 'secret' not in str(url)
    monkeypatch.delenv('DATABASE_PASSWORD')
    with pytest.raises(RuntimeError,match='DATABASE_PASSWORD'):connection_url()

def test_schema_check_requires_migrations(tmp_path,monkeypatch):
    from alembic.config import Config
    from alembic import command
    uri='sqlite:///'+str(tmp_path/'migration.db')
    monkeypatch.setenv('DATABASE_URL',uri)
    engine=create_engine(uri);monkeypatch.setattr(c,'engine',engine)
    assert c.database_status()['status']=='migration_required'
    command.upgrade(Config('apps/api/alembic.ini'),'head')
    assert c.database_status()=={'status':'ready','engine':'sqlite','schema_current':True}
    engine.dispose()

def test_readiness_does_not_invent_connectivity(client,monkeypatch):
    monkeypatch.setattr(c,'database_status',lambda:{'status':'migration_required'})
    monkeypatch.setattr(c,'queue_status',lambda:{'status':'ready'})
    assert client.get('/ready').status_code==503
    monkeypatch.setattr(c,'database_status',lambda:{'status':'ready'})
    assert client.get('/ready').json()['ready'] is True

def test_diagnostics_admin_only(client,mail,monkeypatch):
    assert client.get('/admin/connections').status_code==401
    signup(client,mail)
    assert client.get('/admin/connections').status_code==403
    with Session() as db:
        db.scalar(select(User)).superadmin=True;db.commit()
    monkeypatch.setattr(c,'diagnose',lambda:{'ready':False,'firebase':{'status':'unavailable'}})
    assert client.get('/admin/connections').json()['ready'] is False

def test_firebase_credentials_project_and_redaction(monkeypatch):
    import firebase_admin
    from google.auth.exceptions import DefaultCredentialsError
    monkeypatch.setenv('FIREBASE_AUTH_ENABLED','true')
    monkeypatch.setenv('FIREBASE_PROJECT_ID','expected-project')
    monkeypatch.setenv('FIREBASE_WEB_API_KEY','public-key')
    monkeypatch.setenv('FIREBASE_WEB_APP_ID','app-id')
    wrong=SimpleNamespace(project_id='expected-project',credential=SimpleNamespace(
        get_credential=lambda:SimpleNamespace(project_id='wrong-project')))
    monkeypatch.setattr(firebase_admin,'get_app',lambda name:wrong)
    with pytest.raises(HTTPException) as err:fb.sdk_verify('some-token','expected-project')
    assert err.value.status_code==503
    def missing(project):raise DefaultCredentialsError('SECRET-CONTENTS')
    monkeypatch.setattr(fb,'firebase_app',missing)
    with pytest.raises(HTTPException) as err:fb.sdk_verify('some-token','expected-project')
    assert err.value.status_code==503 and 'SECRET-CONTENTS' not in err.value.detail
    result=c.firebase_status()
    assert result['connected'] is False and 'SECRET-CONTENTS' not in json.dumps(result)

def test_firebase_probe_uses_no_user_listing(monkeypatch):
    from firebase_admin import auth
    monkeypatch.setenv('FIREBASE_AUTH_ENABLED','true')
    monkeypatch.setenv('FIREBASE_PROJECT_ID','fixture-project')
    monkeypatch.setenv('FIREBASE_WEB_API_KEY','public-key')
    monkeypatch.setenv('FIREBASE_WEB_APP_ID','app-id')
    monkeypatch.setattr(fb,'firebase_app',lambda project:object())
    seen=[]
    def get(uid,app):
        seen.append(uid)
        raise auth.UserNotFoundError('not found')
    monkeypatch.setattr(auth,'get_user',get)
    assert c.firebase_status()['connected'] is True
    assert seen[0].startswith('aegis-connection-probe-')
    monkeypatch.setenv('FIREBASE_AUTH_EMULATOR_HOST','localhost:9099')
    assert c.firebase_status()['connected'] is False

def test_failed_services_hide_connection_secrets(monkeypatch):
    import redis
    def fail(*a,**k):raise RuntimeError('SECRET')
    monkeypatch.setattr(redis.Redis,'from_url',fail)
    from aegis import auth
    monkeypatch.setattr(auth,'smtp_connection',fail)
    assert 'SECRET' not in json.dumps(c.queue_status())
    assert c.email_status()=={'status':'unavailable','delivery_tested':False}
