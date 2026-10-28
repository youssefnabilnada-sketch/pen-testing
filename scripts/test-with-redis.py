"""Run the owned-fixture journey against a real, temporary local Redis broker.
Usage: REDIS_SERVER_BINARY=/path/to/redis-server python scripts/test-with-redis.py
Never connects to or flushes an existing Redis service.
"""
import os
import socket
import subprocess
import tempfile
import time
import sys
from pathlib import Path
import redis

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='aegis-redis-test-') as work:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    with open(Path(work)/'redis.log','w+') as log:
        process=subprocess.Popen([os.getenv('REDIS_SERVER_BINARY','redis-server'),
            '--bind','127.0.0.1','--port',str(port),'--save','','--appendonly','no',
            '--protected-mode','yes','--dir',work],stdout=log,stderr=subprocess.STDOUT)
        client=redis.Redis(host='127.0.0.1',port=port,socket_connect_timeout=.2,socket_timeout=.2)
        try:
            for _ in range(100):
                try:
                    if client.ping():break
                except redis.exceptions.ConnectionError:
                    if process.poll() is not None:raise RuntimeError('Temporary Redis failed to start.')
                    time.sleep(.05)
            else:raise RuntimeError('Temporary Redis did not become ready.')
            env={**os.environ,'AEGIS_TEST_BROKER_URL':f'redis://127.0.0.1:{port}/15',
                 'AEGIS_TEST_REDIS_URL':f'redis://127.0.0.1:{port}/14','PYTHONPATH':str(root/'apps/api')}
            extra=['tests/test_native_runtime.py'] if os.getenv('AEGIS_NATIVE_SMOKE')=='1' else []
            code=subprocess.call([sys.executable,'-m','pytest','tests/test_customer_journey.py',
                                  'tests/test_redis_connections.py',*extra,'-q'],cwd=root,env=env)
        finally:
            client.close();process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
raise SystemExit(code)
