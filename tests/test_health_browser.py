"""Real browser/Next/API/HTTP journey; scheduler dispatch is local and deterministic."""
import os
import subprocess
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import httpx
import pytest
import uvicorn
from aegis.main import app
from aegis import safety,health_monitoring as health
from test_assessment import authorized

@pytest.mark.skipif(os.getenv('AEGIS_HEALTH_BROWSER')!='1',reason='Requires built Next and local Chrome')
def test_health_browser(client,mail,monkeypatch,tmp_path):
    monkeypatch.setenv('WEB_ORIGIN','http://127.0.0.1:3001')
    authorized(client,mail,monkeypatch)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.send_response(200);self.end_headers()
        def log_message(self,*args):pass
    fixture=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    ft=threading.Thread(target=fixture.serve_forever,daemon=True);ft.start()
    monkeypatch.setattr(safety,'resolve',lambda origin:('owned.fixture',fixture.server_port,'127.0.0.1','http'))
    monkeypatch.setattr(health.sample,'delay',lambda mid:health.sample(mid))
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8000,log_level='warning'))
    at=threading.Thread(target=server.run,daemon=True);at.start()
    stop=threading.Event();failures=[]
    def schedule():
        while not stop.wait(.3):
            try:health.tick()
            except Exception as exc:failures.append(str(exc));return
    st=threading.Thread(target=schedule,daemon=True);st.start()
    root=Path(__file__).resolve().parents[1];web=root/'apps/web'
    log=open(tmp_path/'next.log','w')
    proc=subprocess.Popen(['node','node_modules/next/dist/bin/next','start','--hostname','127.0.0.1','--port','3001'],cwd=web,stdout=log,stderr=log)
    try:
        with httpx.Client(trust_env=False) as http:
            for _ in range(80):
                try:
                    if http.get('http://127.0.0.1:3001',timeout=1).status_code==200:break
                except httpx.HTTPError:pass
                time.sleep(.25)
            else:raise AssertionError('Next did not start')
        env={**os.environ,'E2E_HEALTH':'1','E2E_BASE_URL':'http://127.0.0.1:3001'}
        result=subprocess.run(['node','node_modules/@playwright/test/cli.js','test','health-local.spec.ts','--workers=1'],cwd=web,env=env,text=True,capture_output=True,timeout=180)
        print(result.stdout,result.stderr)
        assert result.returncode==0
        assert not failures
    finally:
        stop.set();st.join(timeout=10);proc.terminate();proc.wait(timeout=10);log.close()
        server.should_exit=True;at.join(timeout=10);fixture.shutdown();fixture.server_close();ft.join(timeout=3)
