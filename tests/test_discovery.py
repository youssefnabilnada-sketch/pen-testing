import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.discovery import Links
from aegis import safety
from aegis.db import Session
from aegis.models import Authorization,Asset,Setting
from test_assessment import authorized
from conftest import signup

def test_candidates_exclude_external_query_escaped_and_duplicate_paths():
    parser=Links('https://example.test')
    parser.feed('<a href="/help">a</a><a href="/help#part">b</a><a href="https://evil.test/">c</a><a href="/secret?token=x">d</a><a href="/%2e/">e</a><script>location="/never"</script>')
    assert parser.paths==['/help']
    parser.feed(''.join(f'<a href="/path{i}">x</a>' for i in range(50)))
    assert len(parser.paths)==30

def test_discovery_consent_isolation_and_one_use_scope(client,mail,monkeypatch):
    org,asset,_=authorized(client,mail,monkeypatch);calls=[]
    def fetch(origin,**kw):
        calls.append(kw);safety.recheck_authorization()
        return safety.Observation(200,[('Content-Type','text/html')],b'<a href="/help">Help</a>')
    monkeypatch.setattr(safety,'fetch',fetch)
    assert client.post(f'/assets/{asset}/discover-pages',json={'accepted':False}).status_code==403
    result=client.post(f'/assets/{asset}/discover-pages',json={'accepted':True})
    assert result.status_code==200 and result.json()['paths']==['/help'] and len(calls)==1
    with Session() as db:
        auth=db.get(Authorization,result.json()['authorization_id']);assert auth.revoked and auth.scope['paths']==['/']
    outsider=TestClient(app);signup(outsider,mail,'outsider@example.test')
    assert outsider.post(f'/assets/{asset}/discover-pages',json={'accepted':True}).status_code==403
    assert len(calls)==1

@pytest.mark.parametrize('mode',['expired','paused','non_html','timeout'])
def test_failure_never_authorizes_candidates(client,mail,monkeypatch,mode):
    org,asset,_=authorized(client,mail,monkeypatch)
    with Session() as db:
        if mode=='expired':db.get(Asset,asset).verified_until=0
        if mode=='paused':db.add(Setting(key='scans_paused',value=True))
        db.commit()
    def fetch(origin,**kw):
        safety.recheck_authorization()
        if mode=='timeout':raise TimeoutError()
        return safety.Observation(200,[('Content-Type','application/json')],b'{}')
    monkeypatch.setattr(safety,'fetch',fetch)
    assert client.post(f'/assets/{asset}/discover-pages',json={'accepted':True}).status_code in (403,422)
    with Session() as db:
        assert all(a.revoked for a in db.scalars(select(Authorization)) if a.scope.get('purpose')=='link-discovery')

def test_transport_requires_explicit_discovery_scope():
    with pytest.raises(safety.UnsafeTarget):safety.fetch('https://example.test',discovery=True)
