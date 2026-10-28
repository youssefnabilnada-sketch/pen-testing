import time
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from aegis import safety,health_monitoring as health
from aegis.db import Session
from aegis.main import app
from aegis.models import HealthMonitor,HealthSample,Authorization,Notification
from conftest import signup
from test_assessment import authorized

def test_monitor_consent_incident_recovery_and_separate_scope(client,mail,monkeypatch):
    org,asset,_=authorized(client,mail,monkeypatch)
    url=f'/assets/{asset}/health-monitor'
    assert client.put(url,json={'accepted':False}).status_code==403
    assert client.put(url,json={'accepted':True,'interval_seconds':1}).status_code==422
    mid=client.put(url,json={'accepted':True,'path':'/health'}).json()['id']
    with Session() as db:aid=db.get(HealthMonitor,mid).authorization_id
    assert client.post(f'/assets/{asset}/assessments',json={'authorization_id':aid}).status_code==403
    calls=[]
    def fetch(origin,path,**kwargs):
        calls.append(path);return safety.Observation(503,[],b'')
    monkeypatch.setattr(safety,'fetch',fetch)
    health.sample(mid);health.sample(mid)
    assert calls==['/health']
    first=client.get(f'/health-monitors/{mid}/samples').json()[0]
    assert first['status']=='down' and first['incident'] and first['domain_expiration'] is None
    pdf=client.get(f'/health-monitors/{mid}/report.pdf')
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    assert pdf.headers['cache-control']=='no-store'
    with Session() as db:db.get(HealthMonitor,mid).next_due=0;db.commit()
    monkeypatch.setattr(safety,'fetch',lambda *a,**kw:safety.Observation(200,[],b'',{'expires':time.time()+90*86400}))
    health.sample(mid)
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(Notification).where(Notification.kind=='health_change'))==2
    latest=client.get(f'/health-monitors/{mid}/samples').json()[0]
    assert latest['status']=='up' and latest['tls_expires'] and latest['response_ms']>=0
    assert len(client.get(f'/organizations/{org}/health-monitors').json())==1
    assert client.delete(f'/health-monitors/{mid}').status_code==200
    with Session() as db:assert db.get(Authorization,aid).revoked

def test_health_revocation_during_fetch_never_persists_measurement(client,mail,monkeypatch):
    _,asset,_=authorized(client,mail,monkeypatch)
    mid=client.put(f'/assets/{asset}/health-monitor',json={'accepted':True}).json()['id']
    def fetch(*args,**kwargs):
        with Session() as db:
            db.get(Authorization,db.get(HealthMonitor,mid).authorization_id).revoked=True;db.commit()
        return safety.Observation(200,[],b'')
    monkeypatch.setattr(safety,'fetch',fetch);health.sample(mid)
    assert client.get(f'/health-monitors/{mid}/samples').json()==[]
    with Session() as db:assert db.get(HealthMonitor,mid).last_status=='blocked'

def test_health_tenant_isolation(client,mail,monkeypatch):
    org,asset,_=authorized(client,mail,monkeypatch)
    mid=client.put(f'/assets/{asset}/health-monitor',json={'accepted':True}).json()['id']
    other=TestClient(app);signup(other,mail,'health-outsider@example.test')
    assert other.get(f'/organizations/{org}/health-monitors').status_code==403
    assert other.get(f'/health-monitors/{mid}/samples').status_code==403
    assert other.get(f'/health-monitors/{mid}/report.pdf').status_code==403
    assert client.get(f'/health-monitors/{mid}/report.pdf').status_code==200
    assert other.delete(f'/health-monitors/{mid}').status_code==403
    assert other.put(f'/assets/{asset}/health-monitor',json={'accepted':True}).status_code==403


def test_tls_alert_is_deduplicated_and_scheduler_enqueues(client,mail,monkeypatch):
    _,asset,_=authorized(client,mail,monkeypatch)
    mid=client.put(f'/assets/{asset}/health-monitor',json={'accepted':True}).json()['id']
    queued=[]
    monkeypatch.setattr(health.sample,'delay',lambda mid:queued.append(mid))
    health.tick()
    assert queued==[mid]
    expiry=time.time()+10*86400
    monkeypatch.setattr(safety,'fetch',lambda *a,**kw:safety.Observation(200,[],b'',{'expires':expiry}))
    health.sample(mid)
    with Session() as db:db.get(HealthMonitor,mid).next_due=0;db.commit()
    health.sample(mid)
    with Session() as db:
        alerts=list(db.scalars(select(Notification).where(Notification.kind=='health_change')))
        assert len(alerts)==1 and alerts[0].title=='TLS certificate expires soon'


def test_scheduled_health_real_local_http_downtime_recovery(client,mail,monkeypatch):
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    from threading import Thread
    state={'status':503,'paths':[]}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            state['paths'].append(self.path)
            self.send_response(state['status']);self.end_headers()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        org,asset,_=authorized(client,mail,monkeypatch)
        # Test-only transport seam pins this owned fixture; production SSRF policy is unchanged.
        monkeypatch.setattr(safety,'resolve',lambda origin:('owned.fixture',server.server_port,'127.0.0.1','http'))
        mid=client.put(f'/assets/{asset}/health-monitor',json={'accepted':True,'path':'/health'}).json()['id']
        monkeypatch.setattr(health.sample,'delay',lambda mid:health.sample(mid))
        health.tick()
        assert client.get(f'/health-monitors/{mid}/samples').json()[0]['status']=='down'
        state['status']=200
        with Session() as db:db.get(HealthMonitor,mid).next_due=0;db.commit()
        health.tick()
        assert client.get(f'/health-monitors/{mid}/samples').json()[0]['status']=='up'
        assert state['paths']==['/health','/health']
        client.delete(f'/health-monitors/{mid}')
        with Session() as db:db.get(HealthMonitor,mid).next_due=0;db.commit()
        health.tick()
        assert state['paths']==['/health','/health']
    finally:server.shutdown();server.server_close();thread.join(timeout=3)


def test_ssl_failure_alert_and_recovery(client,mail,monkeypatch):
    import ssl
    _,asset,_=authorized(client,mail,monkeypatch)
    mid=client.put(f'/assets/{asset}/health-monitor',json={'accepted':True}).json()['id']
    def bad_tls(*a,**kw):raise ssl.SSLCertVerificationError('Controlled invalid certificate')
    monkeypatch.setattr(safety,'fetch',bad_tls);health.sample(mid)
    assert client.get(f'/health-monitors/{mid}/samples').json()[0]['status']=='tls_error'
    with Session() as db:db.get(HealthMonitor,mid).next_due=0;db.commit()
    monkeypatch.setattr(safety,'fetch',lambda *a,**kw:safety.Observation(200,[],b''));health.sample(mid)
    with Session() as db:
        titles=list(db.scalars(select(Notification.title).where(Notification.kind=='health_change')))
        assert set(titles)=={'Website health incident','Website recovered'}
