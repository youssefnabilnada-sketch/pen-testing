"""API + real owned HTTP fixture + in-memory Celery journey.
Not a browser, Docker, PostgreSQL, Redis, Firebase or public-target acceptance claim.
"""
import time
import os
from celery.contrib.testing.worker import start_worker
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import Job,User
from aegis.worker import celery
from aegis import monitoring
from conftest import signup
from test_live_fixture import live


def wait_job(jid):
    until=time.monotonic()+15
    while time.monotonic()<until:
        with Session() as db:
            status=db.get(Job,jid).status
        if status in ('completed','failed','cancelled'):
            assert status=='completed'
            return
        time.sleep(.1)
    raise AssertionError('Controlled fixture assessment did not finish')


def test_customer_to_engineer_to_full_retest(live,client,mail,monkeypatch):
    org=signup(client,mail)
    asset=client.post(f'/organizations/{org}/assets',json={'origin':'http://fixture.test'}).json()['id']
    challenge=client.post(f'/assets/{asset}/challenge',json={'method':'file'}).json()
    live['token']=challenge['token']
    assert client.post(f'/assets/{asset}/verify/{challenge["id"]}').status_code==200
    auth=client.post(f'/assets/{asset}/authorize',json={'accepted':True}).json()['id']
    broker=celery.conf.broker_url;celery.conf.broker_url=os.getenv('AEGIS_TEST_BROKER_URL','memory://')
    try:
        with start_worker(celery,pool='solo',perform_ping_check=False,concurrency=1):
            launched=client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth})
            assert launched.status_code==201
            jid=launched.json()['id'];wait_job(jid)
            findings=client.get(f'/organizations/{org}/findings').json()
            original=next(f for f in findings if f['rule']=='header.csp')
            assert client.get(f'/assessments/{jid}/report').content.startswith(b'%PDF')
            rid=client.post('/remediations',json={'finding_id':original['id']}).json()['id']
            staff=TestClient(app);signup(staff,mail,'staff@example.test')
            with Session() as db:
                db.scalar(select(User).where(User.email=='staff@example.test')).superadmin=True;db.commit()
            assert staff.post(f'/admin/remediations/{rid}/quote',json={'scope':'Review approved local fixture header changes, rollback and full retesting.','amount_minor':0}).status_code==200
            assert client.post(f'/remediations/{rid}/decision',json={'accept':True}).status_code==200
            assert client.patch(f'/remediations/{rid}/task',json={'status':'in_progress'}).status_code==200
            # Only this test's owned local server changes, following accepted scope.
            live['hardened']=True
            change=client.post(f'/remediations/{rid}/applied',json={
                'evidence':'Approved owned fixture header configuration updated.',
                'rollback_plan':'Set fixture hardened flag false to restore previous headers.',
                'staging_validation':'Controlled fixture configuration inspected; request full supported retest.'})
            assert change.status_code==200
            tid=change.json()['id']
            with Session() as db:
                db.get(Job,jid).created-=120;db.commit()
            approved=client.post(f'/retests/{tid}/approve',json={'accepted':True,'authorization_id':auth})
            assert approved.status_code==200
            # Execute durable dispatch locally; actual assess task still runs through Celery.
            monitoring.dispatch_outbox()
            next_jid=approved.json()['job_id'];wait_job(next_jid)
            retest=client.get(f'/remediations/{rid}/retests').json()[0]
            assert retest['id']==tid and retest['status']=='verified_original'
            assert 'header.csp' in retest['comparison']['resolved']
            assert 'transport.http' in retest['comparison']['unresolved']
            assert retest['report_available']
            assert client.get(f'/assessments/{next_jid}/report').content.startswith(b'%PDF')
            # HTTP fixture still lacks HTTPS: never pretend the full site is fixed.
            assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409
            outsider=TestClient(app);signup(outsider,mail,'outsider@example.test')
            assert outsider.get(f'/remediations/{rid}/retests').status_code==403
            assert outsider.get(f'/assessments/{next_jid}/report').status_code==403
            assert client.get('/health').json()['payments_enabled'] is False
            assert len(live['requests'])==3 # proof + one baseline + one full supported retest
    finally:
        celery.conf.broker_url=broker
