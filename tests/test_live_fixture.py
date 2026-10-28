"""Integration using real loopback HTTP owned by this test, with an explicit injected
transport destination ONLY inside pytest. Production has no localhost override.
"""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from aegis import safety, verification, worker
from aegis.checks import analyze
from aegis.safety import UnsafeTarget
from conftest import signup
import pytest

@pytest.fixture
def live(monkeypatch):
    state={'token':'test-token-which-is-long-enough','hardened':False,'requests':[]}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            state['requests'].append(self.path)
            if self.path=='/':
                self.send_response(200)
                self.send_header('Content-Type','text/html')
                if state['hardened']:
                    self.send_header('Set-Cookie','secret=changed; Secure; HttpOnly')
                    self.send_header('Content-Security-Policy',"default-src 'self'; frame-ancestors 'none'")
                    self.send_header('X-Content-Type-Options','nosniff')
                else:self.send_header('Set-Cookie','secret=SENSITIVE; Path=/')
                self.end_headers()
                self.wfile.write(b'<a href="/help">Help</a><a href="https://outside.test/">External</a>')
                self.wfile.write(f'<meta name="aegis-verification" content="{state["token"]}">'.encode())
            elif self.path==f'/.well-known/aegis-{state["token"]}.txt':
                self.send_response(200);self.end_headers();self.wfile.write(state['token'].encode())
            else:self.send_error(404)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    destination=lambda origin:('fixture.test',server.server_port,'127.0.0.1','http')
    monkeypatch.setattr(safety,'resolve',destination)
    monkeypatch.setattr(verification,'resolve',destination)
    yield state
    server.shutdown();server.server_close();t.join(timeout=2)

def test_real_http_verification_scan_and_retest(live,client,mail,monkeypatch):
    org=signup(client,mail)
    asset=client.post(f'/organizations/{org}/assets',json={'origin':'http://fixture.test'}).json()['id']
    c=client.post(f'/assets/{asset}/challenge',json={'method':'file'}).json()
    live['token']=c['token']
    assert client.post(f'/assets/{asset}/verify/{c["id"]}').status_code==200
    auth=client.post(f'/assets/{asset}/authorize',json={'accepted':True}).json()['id']
    monkeypatch.setattr(worker.assess,'delay',lambda jid:None)
    j=client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth}).json()['id']
    worker.assess(j)
    findings=client.get(f'/organizations/{org}/findings').json()
    assert len(findings)==6
    assert len(live['requests'])==2 # Verification + precisely one assessment request.
    assert 'SENSITIVE' not in str(findings)
    pdf=client.get(f'/assessments/{j}/report').content
    assert pdf.startswith(b'%PDF')
    from pathlib import Path
    Path('docs/testing/local-fixture-report.pdf').write_bytes(pdf)
    live['hardened']=True
    j2=client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth}).json()['id']
    worker.assess(j2)
    f=client.get(f'/organizations/{org}/findings').json()
    assert len([x for x in f if x['status']=='resolved'])==5
    assert next(x for x in f if x['rule']=='transport.http')['status']=='open'
    assert len(live['requests'])==3

def test_real_meta_verification(live):
    c=SimpleNamespace(method='meta',token=live['token'])
    assert verification.verify('http://fixture.test',c)
    c.token='different-token';assert not verification.verify('http://fixture.test',c)


def test_real_discovery_reads_root_without_fetching_links(live,client,mail):
    org=signup(client,mail)
    asset=client.post(f'/organizations/{org}/assets',json={'origin':'http://fixture.test'}).json()['id']
    challenge=client.post(f'/assets/{asset}/challenge',json={'method':'file'}).json()
    live['token']=challenge['token']
    assert client.post(f'/assets/{asset}/verify/{challenge["id"]}').status_code==200
    result=client.post(f'/assets/{asset}/discover-pages',json={'accepted':True})
    assert result.status_code==200,result.text
    assert result.json()['paths']==['/help']
    assert live['requests']==[f'/.well-known/aegis-{challenge["token"]}.txt','/']
