from types import SimpleNamespace
import pytest
from sqlalchemy import select
from aegis.windows import next_allowed,require_window
from aegis.db import Session
from aegis.models import Authorization,AssessmentSchedule
from aegis import worker,monitoring
from test_assessment import authorized,launch

def test_utc_window_boundaries_and_invalid_scope():
    day=20000*86400
    scope={'daily_window_utc':[9,17],'window_start':day}
    assert next_allowed(scope,day+8*3600)==day+9*3600
    assert next_allowed(scope,day+9*3600)==day+9*3600
    assert next_allowed(scope,day+17*3600-5)==day+86400+9*3600
    with pytest.raises(ValueError):require_window(SimpleNamespace(scope=scope,expires=day+86400),day+18*3600)
    with pytest.raises(ValueError):next_allowed({'daily_window_utc':[17,9]},day)
    with pytest.raises(ValueError):require_window(SimpleNamespace(scope={},expires=day+5),day)

def test_worker_never_fetches_outside_window(client,mail,monkeypatch):
    org,asset,authorization=authorized(client,mail,monkeypatch)
    jid=launch(client,asset,authorization)
    with Session() as db:
        auth=db.get(Authorization,authorization);auth.scope={**auth.scope,'window_start':worker.time.time()+100};db.commit()
    called=[]
    def forbidden(*args):
        called.append(args)
        raise AssertionError('No network assessment may run outside consent window')
    monkeypatch.setattr(worker,'fetch',forbidden)
    worker.assess(jid)
    result=client.get(f'/organizations/{org}/assessments').json()[0]
    assert result['status']=='failed'
    assert called==[]
    assert 'outside its approved time window' in result['error']
    assert 'No security assessment result was produced.' in result['error']

def test_scheduler_waits_and_scope_is_persisted(client,mail,monkeypatch):
    org,asset,_=authorized(client,mail,monkeypatch)
    now=monitoring.time.time();hour=int(now%86400//3600)
    start=(hour+2)%24;end=start+1
    response=client.post(f'/assets/{asset}/schedule',json={'accepted':True,'cadence':'daily','start_hour_utc':start,'end_hour_utc':end})
    assert response.status_code==200
    assert response.json()['scope']['daily_window_utc']==[start,end]
    monkeypatch.setattr(monitoring.dispatch_outbox,'delay',lambda:None)
    assert monitoring.monitor_tick()==[]
    with Session() as db:
        schedule=db.scalar(select(AssessmentSchedule));assert schedule.status=='waiting_window' and schedule.next_due>now
    assert client.get(f'/organizations/{org}/intelligence').json()['schedules'][0]['daily_window_utc']==[start,end]
    assert client.post(f'/assets/{asset}/schedule',json={'accepted':True,'cadence':'daily','start_hour_utc':20,'end_hour_utc':4}).status_code==422

def test_transport_rechecks_after_dns_before_any_connection(monkeypatch):
    from aegis import safety
    checked=[];connected=[]
    def guard():
        checked.append(True)
        if len(checked)==2:raise ValueError('Window expired during DNS')
    monkeypatch.setattr(safety,'resolve',lambda _:('fixture.test',80,'93.184.216.34','http'))
    monkeypatch.setattr(safety.socket,'create_connection',lambda *a,**k:connected.append(True))
    with safety.authorization_guard(guard):
        with pytest.raises(ValueError,match='Window expired'):safety.fetch('http://fixture.test')
    assert connected==[]
    safety.recheck_authorization() # Context must be cleared after failure.
