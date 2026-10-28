import json
import time
import pytest
from conftest import signup
from test_intelligence import as_admin
from test_monitoring_regression import setup_fix,applied,approve,age_jobs
from aegis.db import Session
from aegis.models import Job, Retest, Notification
from sqlalchemy import select
from aegis import worker


def test_operations_permissions_bounds_and_redaction(client,mail):
    assert client.get('/admin/operations').status_code==401
    signup(client,mail)
    assert client.get('/admin/operations').status_code==403
    assert client.get('/admin/operations/records/users').status_code==403
    as_admin(client)
    data=client.get('/admin/operations').json()
    assert data['users']==1 and data['organizations']==1 and data['jobs']=={}
    result=client.get('/admin/operations/records/users').json()
    assert result['total']==1 and result['items'][0]['email']=='owner@example.test'
    assert set(result['items'][0])=={'id','email','display_name','verified','active','superadmin','created'}
    assert 'Long-password' not in json.dumps(result)
    assert client.get('/admin/operations/records/users?offset=1').json()['items']==[]
    assert client.get('/admin/operations/records/users?limit=101').status_code==422
    assert client.get('/admin/operations/records/users?offset=-1').status_code==422
    assert client.get('/admin/operations/records/sessions').status_code==404


def test_recover_stale_retest_is_unverified_and_cannot_resume(client,mail,monkeypatch):
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    tid=applied(client,rid);age_jobs();jid=approve(client,tid,auth)
    with Session() as db:
        j=db.get(Job,jid);j.created=time.time()-600;j.status='running';db.commit()
    assert client.post('/admin/recover-stale-jobs').json()['recovered']==1
    with Session() as db:
        job=db.get(Job,jid)
        assert job.cancel and job.status=='failed'
        assert db.get(Retest,tid).status=='unverified'
        assert db.scalar(select(Notification).where(Notification.dedupe_key=='job-failure:'+jid))
        with pytest.raises(worker.AlreadyTerminal):worker.checkpoint(db,job,'running',25)
    calls=[];monkeypatch.setattr(worker,'fetch',lambda origin:calls.append(origin))
    worker.assess(jid)
    assert calls==[]
    assert client.post('/admin/recover-stale-jobs').json()['recovered']==0
    data=client.get('/admin/operations').json()
    assert data['jobs']['failed']==1 and data['jobs']['completed']==1
