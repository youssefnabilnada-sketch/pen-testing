import pytest
from aegis import safety
from aegis.safety import canonical_origin, resolve, UnsafeTarget
from aegis.verification import Meta
from conftest import signup
from aegis.db import Session
from aegis.models import Challenge

@pytest.mark.parametrize('url',['http://user:pw@example.com','file:///etc/passwd','http://127.0.0.1:8080','http://example.com/admin','http://example.com?x=1','http://example.com#x','http://example.com\\@localhost','http://example.com%2f','http://example.com.','http://[::1]','http://x..com'])
def test_ambiguous_urls(url):
    with pytest.raises(UnsafeTarget):
        canonical_origin(url)

@pytest.mark.parametrize('address',['127.0.0.1','10.0.0.1','169.254.169.254','192.168.1.1','0.0.0.0','::1','::ffff:127.0.0.1','224.0.0.1','fc00::1','100.64.0.1'])
def test_private_rejected(monkeypatch,address):
    monkeypatch.setattr(safety.socket,'getaddrinfo',lambda *a,**kw:[(None,None,None,None,(address,80))])
    with pytest.raises(UnsafeTarget):
        resolve('http://example.com')

def test_mixed_dns_and_fixture_exception(monkeypatch):
    monkeypatch.setattr(safety.socket,'getaddrinfo',lambda *a,**kw:[(None,None,None,None,('93.184.216.34',80)),(None,None,None,None,('127.0.0.1',80))])
    with pytest.raises(UnsafeTarget):resolve('https://example.com')
    monkeypatch.setenv('LOCAL_FIXTURE_MODE','true')
    monkeypatch.setattr(safety.socket,'getaddrinfo',lambda *a,**kw:[(None,None,None,None,('172.29.0.10',80))])
    assert resolve('http://fixture')[2]=='172.29.0.10'
    with pytest.raises(UnsafeTarget):resolve('http://other')

def test_pinned_transport_and_redirect(monkeypatch):
    calls=[]
    class Sock:
        def close(self):pass
    class Response:
        status=302
    class Conn:
        def __init__(self,*a,**kw):pass
        def request(self,*a,**kw):calls.append(kw)
        def getresponse(self):return Response()
        def close(self):pass
    monkeypatch.setattr(safety,'resolve',lambda o:('example.com',80,'93.184.216.34','http'))
    monkeypatch.setattr(safety.socket,'create_connection',lambda target,**kw: calls.append(target) or Sock())
    monkeypatch.setattr(safety.http.client,'HTTPConnection',Conn)
    with pytest.raises(UnsafeTarget,match='Redirect'):safety.fetch('http://example.com')
    assert calls[0]==('93.184.216.34',80)
    assert calls[1]['headers']['Host']=='example.com'

def test_unapproved_path():
    with pytest.raises(UnsafeTarget):safety.fetch('https://example.com','/admin')

def test_asset_authorization_expiry_and_revoke(client,mail,monkeypatch):
    org=signup(client,mail)
    monkeypatch.setattr(safety,'resolve',lambda origin:('example.com',443,'93.184.216.34','https'))
    a=client.post(f'/organizations/{org}/assets',json={'origin':'https://example.com'}).json()['id']
    assert client.post(f'/assets/{a}/authorize',json={'accepted':True}).status_code==403
    c=client.post(f'/assets/{a}/challenge',json={'method':'file'}).json()['id']
    monkeypatch.setattr('aegis.verification.verify',lambda *a:False)
    assert client.post(f'/assets/{a}/verify/{c}').status_code==400
    monkeypatch.setattr('aegis.verification.verify',lambda *a:True)
    assert client.post(f'/assets/{a}/verify/{c}').status_code==200
    assert client.post(f'/assets/{a}/verify/{c}').status_code==400
    auth=client.post(f'/assets/{a}/authorize',json={'accepted':True}).json()
    assert auth['scope']['paths']==['/'] and auth['scope']['request_limit']==1
    client.post(f'/assets/{a}/revoke')
    assert client.post(f'/assets/{a}/authorize',json={'accepted':True}).status_code==403
    c2=client.post(f'/assets/{a}/challenge',json={'method':'dns'}).json()['id']
    with Session() as db:
        db.get(Challenge,c2).expires=0
        db.commit()
    assert client.post(f'/assets/{a}/verify/{c2}').status_code==400

def test_meta_parser():
    parser=Meta();parser.feed('<meta name="other" content="bad"><meta name="aegis-verification" content="right">')
    assert parser.tokens==['right']
