"""No-network regression tests for actionable, non-leaking failed scan results."""
import ssl
from aegis import worker
from aegis.assessment_failures import NonSuccessResponse, assessment_failure
from aegis.safety import UnsafeTarget, Observation
from test_assessment import authorized, launch


def test_safe_failure_classifications_never_expose_internal_exception_details():
    cases = [
        (UnsafeTarget('Redirect not followed: a separately authorized origin is required.'), 'site_redirect'),
        (UnsafeTarget('Hostname resolution failed.'), 'site_dns'),
        (UnsafeTarget('Private, special-use or internal destinations are blocked.'), 'unsafe_destination'),
        (NonSuccessResponse(401), 'site_access_restricted'),
        (NonSuccessResponse(403), 'site_access_restricted'),
        (NonSuccessResponse(429), 'site_rate_limited'),
        (NonSuccessResponse(503), 'site_server_error'),
        (TimeoutError('sensitive-internal-detail'), 'site_timeout'),
        (ValueError('Target cooldown active. Wait 60 seconds before submitting another assessment.'), 'target_cooldown'),
        (ValueError('Authorization expired, revoked or scope mismatched.'), 'authorization_expired'),
        (ValueError('Scope changed during execution.'), 'scope_changed'),
        (ValueError('sensitive-internal-detail'), 'internal_processing'),
        (RuntimeError('sensitive-internal-detail'), 'internal_processing'),
    ]
    for exc,expected in cases:
        code,message = assessment_failure(exc)
        assert code == expected
        assert message.endswith('No security assessment result was produced.')
        assert 'sensitive-internal-detail' not in message
        assert 'Traceback' not in message


def test_redirected_target_is_not_followed_and_has_actionable_failure(client,mail,monkeypatch):
    org,asset,auth = authorized(client,mail,monkeypatch)
    called=[]
    def blocked(origin):
        called.append(origin)
        raise UnsafeTarget('Redirect not followed: a separately authorized origin is required.')
    monkeypatch.setattr(worker,'fetch',blocked)
    jid=launch(client,asset,auth)
    worker.assess(jid)
    job=client.get(f'/organizations/{org}/assessments').json()[0]
    assert job['status']=='failed' and job['id']==jid
    assert 'website redirected' in job['error']
    assert 'add and verify' in job['error']
    assert called == ['https://example.test']
    assert client.get(f'/organizations/{org}/findings').json()==[]
    assert client.get(f'/assessments/{jid}/report').status_code==404


def test_restricted_http_status_returns_safe_guidance_not_generic_valueerror(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda origin:Observation(403,[],b'private response not stored'))
    jid=launch(client,asset,auth)
    worker.assess(jid)
    job=client.get(f'/organizations/{org}/assessments').json()[0]
    assert job['status']=='failed'
    assert 'HTTP 403' in job['error']
    assert 'without authentication' in job['error']
    assert 'private response' not in str(job)
    assert client.get(f'/organizations/{org}/findings').json()==[]
    assert client.get(f'/assessments/{jid}/report').status_code==404


def test_unknown_valueerror_is_not_leaked_to_customer(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    def fail(origin):
        raise ValueError('internal sensitive settings from customer or infrastructure')
    monkeypatch.setattr(worker,'fetch',fail)
    jid=launch(client,asset,auth)
    worker.assess(jid)
    job=client.get(f'/organizations/{org}/assessments').json()[0]
    assert job['status']=='failed'
    assert 'processing error' in job['error']
    assert 'internal sensitive settings' not in job['error']
    assert 'ValueError' not in job['error']
