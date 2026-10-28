"""Optional real Redis checks, provisioned by scripts/test-with-redis.py only."""
import os
import pytest
from fastapi import HTTPException
from aegis import connections, main

@pytest.mark.skipif(not os.getenv('AEGIS_TEST_REDIS_URL'),reason='Run scripts/test-with-redis.py for an isolated real Redis')
def test_actual_redis_health_and_rate_limit(monkeypatch):
    monkeypatch.setenv('REDIS_URL',os.environ['AEGIS_TEST_REDIS_URL'])
    monkeypatch.delenv('TESTING',raising=False)
    assert connections.queue_status()['status']=='ready'
    for _ in range(12):main.throttle('isolated-test')
    with pytest.raises(HTTPException) as err:main.throttle('isolated-test')
    assert err.value.status_code==429
