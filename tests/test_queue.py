"""Real Celery worker with an in-memory broker, not a Redis integration claim."""
import time
from celery.contrib.testing.worker import start_worker
from aegis.worker import celery, assess
from aegis.db import Session
from aegis.models import Job
from test_assessment import authorized, BAD
from aegis import worker

def test_celery_queue_executes_persisted_job(client,mail,monkeypatch):
    real_delay=assess.delay
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(assess,'delay',real_delay)
    monkeypatch.setattr(worker,'fetch',lambda origin:BAD)
    previous=celery.conf.broker_url
    celery.conf.broker_url='memory://'
    try:
        with start_worker(celery,pool='solo',perform_ping_check=False,concurrency=1):
            result=client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth})
            assert result.status_code==201,result.text
            jid=result.json()['id']
            deadline=time.monotonic()+12
            status='queued'
            while time.monotonic()<deadline:
                with Session() as db:status=db.get(Job,jid).status
                if status in ('completed','failed'):break
                time.sleep(.1)
            assert status=='completed'
    finally:
        celery.conf.broker_url=previous
