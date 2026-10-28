"""Opt-in real child-process integration; uses the configured isolated database; not browser acceptance."""
import os
import re
import sys
import time
import socket
import subprocess
from pathlib import Path
import httpx
import pytest
from celery import Celery
from test_smtp_delivery import smtp_inbox

pytestmark=pytest.mark.skipif(os.getenv('AEGIS_NATIVE_SMOKE')!='1',reason='Requires built Next app and isolated Redis; use test-with-redis.py with AEGIS_NATIVE_SMOKE=1')

def test_real_frontend_api_worker_registration(smtp_inbox,tmp_path):
    root=Path(__file__).resolve().parents[1]
    for port in (8000,3001):
        with socket.socket() as sock:sock.bind(('127.0.0.1',port))
    env={**os.environ,'PYTHONPATH':str(root/'apps/api'),'REDIS_URL':os.environ['AEGIS_TEST_BROKER_URL'],'NODE_OPTIONS':'--dns-result-order=ipv4first','NEXT_TELEMETRY_DISABLED':'1'}
    processes=[];logs=[]
    def start(name,args,cwd=root):
        log=open(tmp_path/(name+'.log'),'w+');logs.append((name,log))
        p=subprocess.Popen(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(p);return p
    def ready(url,p):
        with httpx.Client(trust_env=False,timeout=2) as client:
            for _ in range(80):
                assert p.poll() is None,'Child service exited'
                try:
                    if client.get(url).status_code==200:return
                except httpx.HTTPError:pass
                time.sleep(.25)
        raise AssertionError('Service readiness timeout')
    try:
        api=start('api',[sys.executable,'-m','uvicorn','aegis.main:app','--host','127.0.0.1','--port','8000']);ready('http://127.0.0.1:8000/health',api)
        worker=start('worker',[sys.executable,'-m','celery','-A','aegis.worker.celery','worker','--pool=solo','--concurrency=1','--loglevel=WARNING'])
        control=Celery('runtime-test',broker=env['REDIS_URL'])
        for _ in range(20):
            if control.control.ping(timeout=1):break
            assert worker.poll() is None
        else:raise AssertionError('Real worker did not respond through Redis')
        web=start('web',['node',str(root/'apps/web/node_modules/next/dist/bin/next'),'start','--hostname','127.0.0.1','--port','3001'],root/'apps/web');ready('http://127.0.0.1:3001',web)
        with httpx.Client(base_url='http://127.0.0.1:3001',trust_env=False,timeout=10) as client:
            assert client.get('/console').status_code==200
            assert client.get('/api/health').status_code==200
            credentials={'email':'native@example.test','password':'Native-test-password-123!'}
            assert client.post('/api/auth/register',json=credentials).status_code==201
            assert len(smtp_inbox)==1
            text=smtp_inbox[0].get_body(preferencelist=('plain',)).get_content()
            token=re.search(r'#verify=([A-Za-z0-9_-]+)',text).group(1)
            assert client.post('/api/auth/verify',json={'token':token}).status_code==200
            result=client.post('/api/auth/login',json=credentials);assert result.status_code==200
            client.headers['X-CSRF-Token']=result.json()['csrf']
            assert client.post('/api/organizations',json={'name':'Native fixture'}).status_code==201
            assert client.get('/api/auth/me').json()['organizations']
            assert client.post('/api/auth/logout').status_code==200
            assert client.get('/api/auth/me').status_code==401
    except Exception:
        for name,log in logs:log.flush();log.seek(0);print(name,log.read()[-4000:])
        raise
    finally:
        for p in reversed(processes):
            p.terminate()
            try:p.wait(timeout=8)
            except subprocess.TimeoutExpired:p.kill();p.wait()
        for _,log in logs:log.close()
