"""Bounded connection diagnostics. Never returns credentials or exception strings."""
import os
import time
import uuid
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from .db import engine

def database_status():
    try:
        config=Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'))
        expected=set(ScriptDirectory.from_config(config).get_heads())
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            current=set(MigrationContext.configure(conn).get_current_heads())
        return {'status':'ready' if current==expected else 'migration_required',
                'engine':engine.dialect.name,'schema_current':current==expected}
    except Exception:
        return {'status':'unavailable','engine':engine.dialect.name,'schema_current':False}

def queue_status():
    import redis
    try:
        with redis.Redis.from_url(os.getenv('REDIS_URL','redis://localhost:6379/0'),
                                 socket_connect_timeout=2,socket_timeout=2) as client:
            client.ping()
            return {'status':'ready','pending_assessments':client.llen('celery'),
                    'pending_intelligence':client.llen('intelligence')}
    except Exception:
        return {'status':'unavailable','pending_assessments':None,'pending_intelligence':None}

def firebase_status():
    if os.getenv('FIREBASE_AUTH_ENABLED')!='true':
        return {'status':'disabled','connected':False}
    from .firebase_identity import config, project_id, firebase_app
    if not config()['enabled']:
        return {'status':'configuration_required','connected':False}
    try:
        from firebase_admin import auth
        app=firebase_app(project_id())
        # A deliberately nonexistent random UID tests Auth access without listing users.
        try:
            auth.get_user('aegis-connection-probe-'+uuid.uuid4().hex,app=app)
        except auth.UserNotFoundError:
            pass
        return {'status':'ready','connected':True,'project':project_id()}
    except Exception:
        return {'status':'unavailable','connected':False,
                'action':'Check server credentials, matching project, Auth permissions and API network access.'}

def email_status():
    try:
        from .auth import smtp_connection
        with smtp_connection() as smtp:
            code,_=smtp.noop()
        return {'status':'ready' if code==250 else 'unavailable','delivery_tested':False}
    except Exception:
        return {'status':'unavailable','delivery_tested':False}

def worker_status():
    try:
        from .worker import celery
        replies=celery.control.inspect(timeout=2).ping() or {}
        names=[name for name,reply in replies.items() if reply.get('ok')=='pong']
        return {'status':'ready' if any(name.startswith('scanner@') for name in names) else 'unavailable',
                'scanner_available':any(name.startswith('scanner@') for name in names),
                'intelligence_available':any(name.startswith('intelligence@') for name in names)}
    except Exception:
        return {'status':'unavailable','scanner_available':False,'intelligence_available':False}

def readiness():
    db=database_status();queue=queue_status()
    return {'ready':db['status']=='ready' and queue['status']=='ready',
            'database':db,'queue':queue,'payments_enabled':False}

def diagnose():
    from .ai_provider import provider_state
    state=readiness()
    state.update(firebase=firebase_status(),email=email_status(),ai=provider_state(),
                 workers=worker_status() if state['queue']['status']=='ready' else
                 {'status':'unavailable','scanner_available':False,'intelligence_available':False},
                 checked_at=time.time())
    state['ready']=state['ready'] and state['workers']['status']=='ready' and state['email']['status']=='ready' and state['firebase']['status'] in ('ready','disabled')
    return state

if __name__=='__main__':
    import json
    result=diagnose()
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['ready'] else 1)
