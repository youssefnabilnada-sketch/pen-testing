import time
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import QueueOutbox,Job,Finding
from aegis import worker,monitoring
from conftest import signup
from test_assessment import authorized
from test_monitoring_regression import setup_fix,applied,age_jobs,approve

def test_broker_failure_survives_and_cancel_blocks_delivery(client,mail,monkeypatch):
    org,a,auth=authorized(client,mail,monkeypatch)
    def fail(*args,**kwargs):raise ConnectionError('unavailable')
    monkeypatch.setattr(worker.assess,'delay',fail)
    r=client.post(f'/assets/{a}/assessments',json={'authorization_id':auth})
    assert r.status_code==201 and r.json()['delivery']=='pending_retry'
    jid=r.json()['id']
    with Session() as db:
        row=db.scalar(select(QueueOutbox).where(QueueOutbox.job_id==jid))
        assert not row.dispatched and row.attempts==1
    assert client.post(f'/assets/{a}/assessments',json={'authorization_id':auth}).status_code==409
    assert client.post(f'/assessments/{jid}/cancel').status_code==200
    with Session() as db:
        db.scalar(select(QueueOutbox).where(QueueOutbox.job_id==jid)).next_attempt=0;db.commit()
    def unexpected(*args,**kwargs):raise AssertionError('cancelled job sent to broker')
    monkeypatch.setattr(worker.assess,'apply_async',unexpected)
    monitoring.dispatch_outbox()
    with Session() as db:
        assert db.get(Job,jid).status=='cancelled'
        assert db.scalar(select(QueueOutbox).where(QueueOutbox.job_id==jid)).dispatched

def test_retest_evidence_recovery_tenant_isolation_and_cancel(client,mail,monkeypatch):
    org,a,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    tid=applied(client,rid)
    path=f'/remediations/{rid}/retests'
    recovered=client.get(path).json()[0]
    assert recovered['id']==tid and 'fixture' in recovered['evidence']
    assert recovered['status']=='awaiting_approval' and not recovered['report_available']
    other=TestClient(app);signup(other,mail,'outside@example.test')
    assert other.get(path).status_code==403
    age_jobs();jid=approve(client,tid,auth)
    assert client.post(f'/assessments/{jid}/cancel').status_code==200
    recovered=client.get(path).json()[0]
    assert recovered['status']=='unverified' and recovered['job_status']=='cancelled'
    assert not recovered['report_available']
    with Session() as db:assert db.get(Finding,fid).status!='resolved'
