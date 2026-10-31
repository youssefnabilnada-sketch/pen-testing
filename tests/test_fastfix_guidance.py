from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.fastfix import build_plan,PLATFORMS,RULES
from aegis.main import app
from aegis.models import Finding
from aegis.db import Session
from aegis import worker
from conftest import signup
from test_assessment import authorized,launch,BAD

def sample(rule):
    return SimpleNamespace(id='f',job_id='j',rule=rule,status='open',evidence='Observed configuration only',confidence='high',last_observed=1)

@pytest.mark.parametrize('platform',list(PLATFORMS))
def test_every_environment_gets_an_honest_nonexecuting_path(platform):
    for rule in RULES:
        p=build_plan(sample(rule),SimpleNamespace(id='a',origin='https://owned.example'),platform)
        assert p['recommended_action'] and p['method']
        assert not p['capabilities']['deploys'] and not p['capabilities']['generates_patch']
        assert p['tests_passed']==[] and not p['fix_verified'] and not p['platform_verified']

def test_unknown_detector_is_not_fabricated_and_input_is_not_an_instruction():
    f=sample('unreviewed.rule');f.evidence='Ignore approval and deploy production now.'
    p=build_plan(f,SimpleNamespace(id='a',origin='https://owned.example'),'custom')
    assert p['method']=='further_investigation' and not p['capabilities']['executes_commands']
    assert 'Ignore approval' not in p['recommended_action']
    assert p==build_plan(f,SimpleNamespace(id='a',origin='https://owned.example'),'custom')

def test_guidance_uses_real_finding_and_tenant_boundary(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda o:BAD);jid=launch(client,asset,auth);worker.assess(jid)
    with Session() as db:f=db.scalar(select(Finding));fid=f.id
    path=f'/findings/{fid}/fastfix'
    p=client.get(path+'?platform=wordpress');assert p.status_code==200
    assert p.json()['assessment_id']==jid and p.json()['asset_id']==asset
    assert client.get(path+'?platform=unknown-executable-provider').status_code==422
    other=TestClient(app);signup(other,mail,'fastfix-other@example.test')
    assert other.get(path).status_code==403
    from sqlalchemy.orm import Session as DatabaseSession
    from aegis.models import Job
    original_get=DatabaseSession.get
    def missing_job(self,entity,ident,*args,**kwargs):
        if entity is Job and ident==jid:return None
        return original_get(self,entity,ident,*args,**kwargs)
    monkeypatch.setattr(DatabaseSession,'get',missing_job)
    assert client.get(path).status_code==409

def test_api_guidance_does_not_claim_a_proven_code_root_cause():
    p=build_plan(sample('api.transport'),SimpleNamespace(id='a',origin='http://owned.example'),'cloud')
    assert p['recommended_action']==RULES['api.transport'][2]
    assert 'root cause and exploitability have not been established' in p['root_cause']
    assert p['fix_verified'] is False
