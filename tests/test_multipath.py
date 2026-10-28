import pytest
from aegis.multipath import validate_paths,combine,qualify
from test_assessment import authorized,BAD
from aegis import worker
@pytest.mark.parametrize('paths',[[{}],[None],['//other'],['/../admin'],['/%2e'],['/?x=1'],['/','/'],[f'/p{i}' for i in range(21)]])
def test_reject_ambiguous_paths(paths):
    with pytest.raises(ValueError):validate_paths(paths)
def test_explicit_paths_execute_with_distinct_findings(client,mail,monkeypatch):
    org,asset,_=authorized(client,mail,monkeypatch)
    auth=client.post(f'/assets/{asset}/authorize',json={'accepted':True,'paths':['/','/help']}).json()['id']
    monkeypatch.setattr(worker.assess,'delay',lambda *a:None)
    calls=[]
    def fetch(origin,path='/',**kwargs):calls.append(path);return BAD
    monkeypatch.setattr(worker,'fetch',fetch)
    job=client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth}).json()['id']
    worker.assess(job)
    assert calls==['/','/help']
    findings=client.get(f'/organizations/{org}/findings').json()
    assert len(findings)==12
    assert any(f['rule']==qualify('header.csp','/help') for f in findings)

def test_omitted_path_remains_unverified_and_explanation_is_supported():
    from aegis.regression import compare
    from aegis.analyst import RuleBasedAnalyst
    rule=qualify('header.csp','/help')
    result=compare([{'rule':rule}],[],{'executed':['header.csp'],'not_performed':{}})
    assert result['resolved']==[] and result['unverified'][0]['rule']==rule
    explanation=RuleBasedAnalyst().explain([rule])
    assert len(explanation['recommendations'])==1
    assert explanation['recommendations'][0]['rule']==rule

def test_transport_rejects_unlisted_path_before_resolution(monkeypatch):
    from aegis import safety
    scope={'origin':'https://fixture.test','type':'explicit-path-response','method':'GET','paths':['/help'],'request_limit':1,'timeout_seconds':5}
    monkeypatch.setattr(safety,'resolve',lambda origin:pytest.fail('Unauthorized DNS request'))
    with pytest.raises(ValueError):safety.fetch('https://fixture.test','/admin',assessment_scope=scope)

@pytest.mark.parametrize('rule',['csp.base-uri','header.csp'])
def test_qualified_catalog_rules_have_guidance(rule):
    from aegis.analyst import RuleBasedAnalyst
    assert RuleBasedAnalyst().explain([qualify(rule,'/help')])['recommendations']

def test_retest_rejects_narrowed_scope(client,mail,monkeypatch):
    from test_monitoring_regression import setup_fix,applied
    from aegis.db import Session
    from aegis.models import Authorization
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    with Session() as db:
        authorization=db.get(Authorization,auth)
        authorization.scope={**authorization.scope,'paths':['/','/help'],'type':'explicit-path-response','request_limit':2}
        db.commit()
    tid=applied(client,rid)
    assert client.get(f'/remediations/{rid}/retests').json()[0]['paths']==['/','/help']
    narrowed=client.post(f'/assets/{asset}/authorize',json={'accepted':True}).json()['id']
    response=client.post(f'/retests/{tid}/approve',json={'accepted':True,'authorization_id':narrowed})
    assert response.status_code==409

def test_full_multipath_retest_preserves_failed_path_and_reports(client,mail,monkeypatch):
    from test_monitoring_regression import setup_fix,applied,approve,age_jobs
    from test_assessment import GOOD
    org,asset,_,rid,_=setup_fix(client,mail,monkeypatch)
    auth=client.post(f'/assets/{asset}/authorize',json={'accepted':True,'paths':['/','/help']}).json()['id']
    age_jobs()
    monkeypatch.setattr(worker,'fetch',lambda origin,path='/',**kw:BAD)
    job=client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth}).json()['id']
    worker.assess(job)
    tid=applied(client,rid);age_jobs()
    retest_job=approve(client,tid,auth)
    calls=[]
    def response(origin,path='/',**kw):
        calls.append(path)
        return GOOD if path=='/' else BAD
    monkeypatch.setattr(worker,'fetch',response)
    worker.assess(retest_job)
    result=client.get(f'/remediations/{rid}/retests').json()[0]
    assert calls==['/','/help']
    assert 'header.csp' in result['comparison']['resolved']
    assert qualify('header.csp','/help') in result['comparison']['unresolved']
    assert result['report_available']
    assert client.get(f'/assessments/{retest_job}/report').content.startswith(b'%PDF')
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409

@pytest.mark.parametrize('failure',['cancel','timeout','scope_change'])
def test_interrupted_paths_never_commit_partial_clean_results(client,mail,monkeypatch,failure):
    from aegis.db import Session
    from aegis.models import Job,Authorization
    org,asset,_=authorized(client,mail,monkeypatch)
    auth=client.post(f'/assets/{asset}/authorize',json={'accepted':True,'paths':['/','/help']}).json()['id']
    monkeypatch.setattr(worker.assess,'delay',lambda *a:None)
    job=client.post(f'/assets/{asset}/assessments',json={'authorization_id':auth}).json()['id']
    calls=[]
    def response(origin,path='/',**kw):
        calls.append(path)
        if failure=='timeout' and path=='/help':raise TimeoutError()
        if path=='/':
            with Session() as db:
                if failure=='cancel':db.get(Job,job).cancel=True
                if failure=='scope_change':
                    a=db.get(Authorization,auth)
                    a.scope={**a.scope,'paths':['/','/other']}
                db.commit()
        return BAD
    monkeypatch.setattr(worker,'fetch',response)
    worker.assess(job)
    with Session() as db:assert db.get(Job,job).status==('cancelled' if failure=='cancel' else 'failed')
    assert calls==(['/','/help'] if failure=='timeout' else ['/'])
    assert client.get(f'/organizations/{org}/findings').json()==[]
    assert client.get(f'/assessments/{job}/report').status_code==404
