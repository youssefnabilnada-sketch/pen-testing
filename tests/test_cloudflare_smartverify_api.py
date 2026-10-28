"""Integration coverage in the full API CI environment; never calls real Cloudflare."""
from fastapi.testclient import TestClient
from aegis.main import app
from aegis import cloudflare_verify as cf
from conftest import signup
from test_onboarding import setup


def test_cloudflare_dns_publish_requires_scope_preview_consent_and_keeps_secret_private(client, mail, monkeypatch):
    asset = setup(client, mail, monkeypatch)
    dns = client.post(f'/assets/{asset}/challenge', json={'method':'dns'}).json()
    base = f'/assets/{asset}/challenge/{dns["id"]}/cloudflare'
    preview = client.get(base + '/preview')
    assert preview.status_code == 200
    assert preview.json()['name'] == '_aegis.example.test'
    assert preview.json()['content'] == 'aegis=' + dns['token']
    token = 'scoped-cloudflare-test-secret'
    body = {'zone_id':'f'*32,'api_token':token}
    assert client.post(base + '/publish', json=body).status_code == 422
    assert client.post(base + '/publish', json={**body,'confirm_dns_change':True,'zone_id':'other'}).status_code == 422
    calls = []
    def remote(method, path, bearer, *, params=None, payload=None):
        assert bearer == token
        calls.append(method)
        if method == 'GET' and path.endswith('/dns_records'):
            return {'result':[], 'result_info':{'total_pages':1}}
        if method == 'GET':
            return {'result':{'name':'example.test'}}
        assert method == 'POST'
        assert payload['type'] == 'TXT' and payload['name'] == '_aegis.example.test'
        return {'result':payload}
    monkeypatch.setattr(cf,'_cloudflare',remote)
    response = client.post(base + '/publish',json={**body,'confirm_dns_change':True})
    assert response.status_code == 200
    assert calls == ['GET','GET','POST']
    assert token not in response.text
    assert response.json()['published'] is True
    # Writing a DNS proof never grants ownership or scan permission without explicit verification.
    assert client.post(f'/assets/{asset}/authorize',json={'accepted':True}).status_code == 403


def test_cloudflare_publish_is_tenant_scoped_and_challenge_bound(client,mail,monkeypatch):
    asset = setup(client,mail,monkeypatch)
    dns = client.post(f'/assets/{asset}/challenge',json={'method':'dns'}).json()
    file_proof = client.post(f'/assets/{asset}/challenge',json={'method':'file'}).json()
    other = TestClient(app)
    signup(other, mail, 'cloudflare-outsider@example.test')
    base = f'/assets/{asset}/challenge/{dns["id"]}/cloudflare'
    assert other.get(base+'/preview').status_code == 403
    assert other.post(base+'/publish',json={
        'zone_id':'f'*32,'api_token':'token-secret-placeholder', 'confirm_dns_change':True}).status_code == 403
    assert client.get(f'/assets/{asset}/challenge/{file_proof["id"]}/cloudflare/preview').status_code == 409
    assert client.get(f'/assets/{asset}/challenge/no-such-challenge/cloudflare/preview').status_code == 404


def test_cloudflare_will_not_write_if_zone_does_not_match(client,mail,monkeypatch):
    asset = setup(client,mail,monkeypatch)
    dns = client.post(f'/assets/{asset}/challenge',json={'method':'dns'}).json()
    calls = []
    def remote(method,path,bearer,**kw):
        calls.append(method)
        return {'result':{'name':'unrelated.invalid'}}
    monkeypatch.setattr(cf,'_cloudflare',remote)
    path = f'/assets/{asset}/challenge/{dns["id"]}/cloudflare/publish'
    response = client.post(path,json={'zone_id':'f'*32,'api_token':'placeholder-token-for-tests',
                                     'confirm_dns_change':True})
    assert response.status_code == 403 and calls == ['GET']
