"""Entrypoint for native Linux services; no containers or public listener defaults."""
import os
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'apps/api'))
if os.getenv('AEGIS_ENV')!='production':raise SystemExit('This entrypoint requires production configuration.')
role=sys.argv[1] if len(sys.argv)==2 else ''
if role!='web':
    # Propagate the trusted role before importing workers or validating settings.
    # A scanner must not require the API's Firebase/MFA/SMTP secrets.
    os.environ['AEGIS_SERVICE_ROLE']=role
    from aegis.runtime import validate_runtime
    validate_runtime()
python=sys.executable
commands={
 'api':[python,'-m','uvicorn','aegis.main:app','--host','127.0.0.1','--port','8000','--workers','2','--proxy-headers','--forwarded-allow-ips','127.0.0.1'],
 'scanner':[python,'-m','celery','-A','aegis.worker.celery','worker','--loglevel=INFO','--concurrency=1','--hostname=scanner@%h'],
 'intelligence':[python,'-m','celery','-A','aegis.worker.celery','worker','-Q','intelligence','--loglevel=INFO','--concurrency=1','--hostname=intelligence@%h'],
 'notifier':[python,'-m','celery','-A','aegis.worker.celery','worker','-Q','notifications','--loglevel=INFO','--concurrency=1','--hostname=notifier@%h'],
 'scheduler':[python,'-m','celery','-A','aegis.worker.celery','beat','--loglevel=INFO','--schedule=/var/lib/aegis-scheduler/beat'],
 'migrate':[python,'-m','alembic','-c',str(root/'apps/api/alembic.ini'),'upgrade','head'],
 'web':['/usr/bin/node',str(root/'apps/web/.next/standalone/server.js')],
}
if role not in commands:raise SystemExit('Choose api, scanner, intelligence, notifier, scheduler or web.')
os.environ['PYTHONPATH']=str(root/'apps/api')
if role=='web':
    os.environ.update(NODE_ENV='production',HOSTNAME='127.0.0.1',PORT='3000')
os.execv(commands[role][0],commands[role])
