from sqlalchemy import select
from aegis.db import Session
from aegis.models import Job,Report,Finding
from aegis import worker
from aegis.safety import Observation
from aegis.api_assessment import profile
from test_assessment import authorized,launch

def test_api_profile_does_not_claim_browser_or_auth_checks():
    found,manifest=profile('https://api.example',Observation(200,[('Content-Type','application/json'),('X-Content-Type-Options','nosniff'),('Access-Control-Allow-Origin','*'),('Access-Control-Allow-Credentials','true')],b'sensitive body'))
    assert [f['rule'] for f in found]==['api.cors_credentials']
    assert 'header.csp' not in manifest['executed']
    assert 'authorization_logic' in manifest['not_performed']
    assert 'sensitive body' not in str((found,manifest))

def test_api_scope_worker_report_and_unsafe_path(client,mail,monkeypatch):
    org,asset,_=authorized(client,mail,monkeypatch)
    assert client.post(f'/assets/{asset}/authorize',json={'accepted':True,'profile':'api','paths':['/logout']}).status_code==422
    auth=client.post(f'/assets/{asset}/authorize',json={'accepted':True,'profile':'api','paths':['/api/health']}).json()
    assert auth['scope']['type']=='api-response-configuration'
    calls=[]
    def fetch(origin,path,**kw):
        calls.append((path,kw['assessment_scope']['type']))
        return Observation(200,[('Content-Type','application/json')],b'PRIVATE')
    monkeypatch.setattr(worker,'fetch',fetch)
    jid=launch(client,asset,auth['id']);worker.assess(jid)
    assert calls==[('/api/health','api-response-configuration')]
    with Session() as db:
        assert db.get(Job,jid).status=='completed'
        report=db.scalar(select(Report).where(Report.job_id==jid))
        assert 'PRIVATE' not in str(report.snapshot)
        assert report.snapshot['scope']['type']=='api-response-configuration'
        assert all(f.rule.startswith('api.') for f in db.scalars(select(Finding)))
    assert client.get(f'/assessments/{jid}/report').status_code==200
