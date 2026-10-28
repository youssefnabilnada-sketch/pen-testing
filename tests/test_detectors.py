import json
import pytest
from conftest import signup
from test_intelligence import as_admin
from aegis.db import Session
from aegis.models import DetectionRule
from aegis.detectors import CATALOG, validate
from aegis.regression import profile, compare
from aegis.checks import analyze
from aegis.safety import Observation


def response(*headers):
    return Observation(200,list(headers),b'')

@pytest.mark.parametrize('key',list(CATALOG))
def test_owned_fixtures(key):
    assert validate(key)>=2


def test_candidate_authorization_activation_disable_and_versions(client,mail):
    signup(client,mail)
    key='csp.base-uri';path='/admin/intelligence/rules/'+key
    assert client.post(path+'/validate').status_code==403
    as_admin(client)
    assert client.post(path+'/approve').status_code==409
    assert client.post(path+'/validate').json()['tests']==4
    assert client.post(path+'/approve').json()['enabled']
    observed=response(('Content-Security-Policy',"default-src 'none'"))
    with Session() as db:
        findings,manifest=profile(db,'https://fixture.test',observed)
        assert key in manifest['executed']
        assert key in [x['rule'] for x in findings]
    assert client.post(path+'/disable').status_code==200
    with Session() as db:
        _,manifest=profile(db,'https://fixture.test',observed)
        assert compare([{'rule':key}],[],manifest)['unverified'][0]['rule']==key
        r=db.get(DetectionRule,key);r.enabled=True;r.test_evidence='[]';db.commit()
    assert client.post(path+'/approve').status_code==409
    with Session() as db:
        assert key not in profile(db,'https://fixture.test',observed)[1]['executed']
        r=db.get(DetectionRule,key);r.test_evidence=json.dumps({'version':'0','tests':4,'result':'passed'});db.commit()
    assert client.post(path+'/approve').status_code==409


def test_default_disabled_and_cookie_evidence(client,mail):
    signup(client,mail);as_admin(client)
    bad=response(('Set-Cookie','fixture=private; Secure; HttpOnly'))
    with Session() as db:
        assert not set(CATALOG)&set(profile(db,'https://fixture.test',bad)[1]['executed'])
    for action in ('validate','approve'):
        assert client.post('/admin/intelligence/rules/cookie.samesite/'+action).status_code==200
    with Session() as db:
        found,manifest=profile(db,'https://fixture.test',bad)
        item=next(f for f in found if f['rule']=='cookie.samesite')
        assert 'private' not in json.dumps(item)
        good=response(('Set-Cookie','fixture=private; Secure; HttpOnly; SameSite=Lax'))
        findings,manifest=profile(db,'https://fixture.test',good)
        assert compare([item],findings,manifest)['resolved']==['cookie.samesite']
        findings,manifest=profile(db,'https://fixture.test',response())
        assert compare([item],findings,manifest)['unverified'][0]['rule']=='cookie.samesite'
        malformed=response(('Set-Cookie','ok=x; Secure; HttpOnly'),('Set-Cookie','invalid'))
        _,manifest=profile(db,'https://fixture.test',malformed)
        assert {'cookie.secure','cookie.httponly','cookie.samesite'}<=set(manifest['not_performed'])


def test_csp_duplicate_directive_and_misleading_substring():
    bad=response(('Content-Security-Policy',"script-src 'unsafe-inline'; script-src 'none'; report-uri /frame-ancestors"))
    rules={f['rule'] for f in analyze('https://fixture.test',bad)}
    assert {'csp.inline','header.frame'}<=rules
    good=response(('Content-Security-Policy',"script-src 'none'; script-src 'unsafe-inline'; frame-ancestors 'none'"))
    assert not {'csp.inline','header.frame'}&{f['rule'] for f in analyze('https://fixture.test',good)}
    multiple=response(('Content-Security-Policy',"script-src 'none'"),('Content-Security-Policy',"script-src 'unsafe-inline'"))
    with Session() as db:
        found,manifest=profile(db,'https://fixture.test',multiple)
        result=compare([{'rule':'csp.inline'},{'rule':'header.frame'}],found,manifest)
        assert result['resolved']==[]
        assert len(result['unverified'])==2


def test_empty_last_policy_does_not_hide_existing_policy():
    observed=response(('Content-Security-Policy',"script-src 'unsafe-inline'"),('Content-Security-Policy',''))
    with Session() as db:
        found,manifest=profile(db,'https://fixture.test',observed)
    assert 'header.csp' not in {f['rule'] for f in found}
    assert 'csp.inline' not in manifest['executed']


def test_failed_revalidation_disables_active_rule(client,mail,monkeypatch):
    from aegis import detectors
    signup(client,mail);as_admin(client)
    path='/admin/intelligence/rules/header.referrer/'
    assert client.post(path+'validate').status_code==200
    assert client.post(path+'approve').status_code==200
    def fail(key):raise ValueError('Fixture failed')
    monkeypatch.setattr(detectors,'validate',fail)
    assert client.post(path+'validate').status_code==409
    with Session() as db:assert not detectors.active(db.get(DetectionRule,'header.referrer'))
