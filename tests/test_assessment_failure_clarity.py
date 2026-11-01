"""Public assessment errors must be helpful without revealing internal diagnostics."""
from aegis.assessment_failures import classify_assessment_failure, public_assessment_error
from aegis.safety import UnsafeTarget, Observation
from aegis import safety, worker
from conftest import signup


def test_safe_classification_of_expected_assessment_errors():
    cases = [
        (UnsafeTarget('Redirect not followed: a separately authorized origin is required.'), 'TARGET_REDIRECT'),
        (UnsafeTarget('Hostname resolution failed.'), 'TARGET_DNS'),
        (UnsafeTarget('Private, special-use or internal destinations are blocked.'), 'TARGET_SCOPE_BLOCKED'),
        (ValueError('Non-success response; no clean result implied.'), 'TARGET_HTTP_RESPONSE'),
        (ValueError('Target cooldown active. Wait 60 seconds before submitting another assessment.'), 'TARGET_COOLDOWN'),
        (ValueError('Authorization expired, revoked or scope mismatched.'), 'AUTHORIZATION_EXPIRED'),
        (ValueError('Scope changed during execution.'), 'AUTHORIZATION_SCOPE'),
        (TimeoutError('private diagnostic'), 'TARGET_TIMEOUT'),
        (ConnectionError('private diagnostic'), 'TARGET_CONNECTION'),
        (ValueError('private internal value = TOP_SECRET'), 'ASSESSMENT_INTERNAL'),
    ]
    for exception, code in cases:
        assert classify_assessment_failure(exception)[0] == code
        public = public_assessment_error(exception)
        assert f'[{code}]' in public
        assert 'No clean result is implied.' in public
        assert 'TOP_SECRET' not in public
        assert 'private diagnostic' not in public


def test_public_error_codes_persist_in_real_failed_job(client, mail, monkeypatch):
    org = signup(client, mail)
    monkeypatch.setattr(safety, 'resolve', lambda origin: ('example.test',443,'93.184.216.34','https'))
    asset = client.post(f'/organizations/{org}/assets',json={'origin':'https://example.test'}).json()['id']
    challenge = client.post(f'/assets/{asset}/challenge',json={'method':'file'}).json()['id']
    monkeypatch.setattr('aegis.verification.verify',lambda *args:True)
    assert client.post(f'/assets/{asset}/verify/{challenge}').status_code == 200
    auth = client.post(f'/assets/{asset}/authorize',json={'accepted':True}).json()['id']
    monkeypatch.setattr(worker.assess,'delay',lambda jid:None)
    job = client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth}).json()['id']
    def blocked_redirect(_origin):
        raise UnsafeTarget('Redirect not followed: a separately authorized origin is required.')
    monkeypatch.setattr(worker,'fetch',blocked_redirect)
    worker.assess(job)
    result = client.get(f'/organizations/{org}/assessments').json()[0]
    assert result['status'] == 'failed'
    assert '[TARGET_REDIRECT]' in result['error']
    assert 'separately authorized origin' not in result['error']
    assert 'No clean result is implied.' in result['error']
    assert client.get(f'/assessments/{job}/report').status_code == 404


def test_non_success_response_is_not_misreported_as_clean_result(client, mail, monkeypatch):
    org = signup(client, mail)
    monkeypatch.setattr(safety, 'resolve', lambda origin: ('example.test',443,'93.184.216.34','https'))
    asset = client.post(f'/organizations/{org}/assets',json={'origin':'https://example.test'}).json()['id']
    challenge = client.post(f'/assets/{asset}/challenge',json={'method':'file'}).json()['id']
    monkeypatch.setattr('aegis.verification.verify',lambda *args:True)
    assert client.post(f'/assets/{asset}/verify/{challenge}').status_code == 200
    auth = client.post(f'/assets/{asset}/authorize',json={'accepted':True}).json()['id']
    monkeypatch.setattr(worker.assess,'delay',lambda jid:None)
    job = client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth}).json()['id']
    monkeypatch.setattr(worker,'fetch',lambda _origin:Observation(403,[],b''))
    worker.assess(job)
    result = client.get(f'/organizations/{org}/assessments').json()[0]
    assert result['status'] == 'failed'
    assert '[TARGET_HTTP_RESPONSE]' in result['error']
    assert 'No clean result is implied.' in result['error']
