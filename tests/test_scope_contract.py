import pytest
from aegis.scope import require_supported_scope
from aegis.db import Session
from aegis.models import Authorization
from aegis import worker
from test_assessment import authorized,launch

@pytest.mark.parametrize('change',[{'paths':['/admin']},{'method':'POST'},{'request_limit':True},{'request_limit':2},{'timeout_seconds':60},{'type':'active'},{'origin':'https://other.test'}])
def test_profile_rejects_unsupported_changes(change):
    scope={'origin':'https://fixture.test','paths':['/'],'method':'GET','type':'root-response-configuration','request_limit':1,'timeout_seconds':5}
    require_supported_scope(scope,'https://fixture.test')
    with pytest.raises(ValueError):require_supported_scope({**scope,**change},'https://fixture.test')

def test_creation_and_worker_recheck_budget(client,mail,monkeypatch):
    org,asset,aid=authorized(client,mail,monkeypatch)
    with Session() as db:
        a=db.get(Authorization,aid);original=dict(a.scope);a.scope={**original,'request_limit':2};db.commit()
    assert client.post(f'/assets/{asset}/assessments',json={'authorization_id':aid}).status_code==403
    with Session() as db:db.get(Authorization,aid).scope=original;db.commit()
    job=launch(client,asset,aid)
    with Session() as db:db.get(Authorization,aid).scope={**original,'method':'POST'};db.commit()
    calls=[];monkeypatch.setattr(worker,'fetch',lambda origin:calls.append(origin))
    worker.assess(job)
    assert calls==[]
    assert client.get(f'/organizations/{org}/assessments').json()[0]['status']=='failed'

@pytest.mark.parametrize('change',[{'method':'POST'},{'request_limit':2},{'paths':['/other']},{'timeout_seconds':60}])
def test_scheduled_and_retest_enqueue_rejects_unsupported_scope(client,mail,monkeypatch,change):
    from aegis.monitoring import enqueue
    from aegis.models import Asset,Job,QueueOutbox
    from sqlalchemy import select,func
    org,asset,aid=authorized(client,mail,monkeypatch)
    with Session() as db:
        auth=db.get(Authorization,aid);auth.scope={**auth.scope,**change};db.commit()
        with pytest.raises(ValueError):enqueue(db,db.get(Asset,asset),aid)
        assert db.scalar(select(func.count()).select_from(Job))==0
        assert db.scalar(select(func.count()).select_from(QueueOutbox))==0
