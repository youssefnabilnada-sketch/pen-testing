import time
from sqlalchemy import select
from aegis import worker,monitoring,verification
from aegis.db import Session
from aegis.models import User, Job, Finding, Remediation, Retest, Authorization, Asset, AssessmentSchedule, QueueOutbox, Notification, IntelligenceSource
from aegis.safety import Observation
from aegis.intelligence import service
from test_assessment import authorized,launch,BAD,GOOD
from test_intelligence import as_admin,store_example


def age_jobs():
    with Session() as db:
        for j in db.scalars(select(Job)):j.created-=120
        db.commit()


def setup_fix(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda o:BAD);jid=launch(client,asset,auth);worker.assess(jid)
    f=next(x for x in client.get(f'/organizations/{org}/findings').json() if x['rule']=='header.csp')
    rid=client.post('/remediations',json={'finding_id':f['id']}).json()['id']
    as_admin(client)
    assert client.post(f'/admin/remediations/{rid}/quote',json={'scope':'Approved staging-only configuration remediation and full regression assessment','amount_minor':0}).status_code==200
    client.post(f'/remediations/{rid}/decision',json={'accept':True})
    client.patch(f'/remediations/{rid}/task',json={'status':'in_progress'})
    monkeypatch.setattr(monitoring.dispatch_outbox,'delay',lambda:None)
    return org,asset,auth,rid,f['id']


def applied(client,rid):
    result=client.post(f'/remediations/{rid}/applied',json={'evidence':'Engineer changed isolated fixture response headers only.', 'rollback_plan':'Restore the prior fixture configuration from the approved local copy.', 'staging_validation':'Approved isolated fixture tests passed before requesting full security reassessment.'})
    assert result.status_code==200,result.text
    return result.json()['id']


def approve(client,tid,auth):
    result=client.post(f'/retests/{tid}/approve',json={'accepted':True,'authorization_id':auth})
    assert result.status_code==200,result.text
    return result.json()['job_id']


def test_full_reassessment_success_comparison_and_closure(client,mail,monkeypatch):
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    tid=applied(client,rid)
    assert client.post(f'/retests/{tid}/approve',json={'accepted':False,'authorization_id':auth}).status_code==409
    age_jobs();jid=approve(client,tid,auth)
    monkeypatch.setattr(worker,'fetch',lambda o:GOOD);worker.assess(jid)
    data=client.get(f'/organizations/{org}/intelligence').json();r=data['retests'][0]
    assert r['status']=='verified_original',r
    assert len(r['comparison']['resolved'])==6 and r['comparison']['unresolved']==[]
    assert set(r['comparison']['profile']['executed'])>=set(x['rule'] for x in BAD_findings())
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==200
    pdf=client.get(f'/assessments/{jid}/report').content
    assert pdf.startswith(b'%PDF')
    from pathlib import Path
    Path('docs/testing/full-retest-report.pdf').write_bytes(pdf)
    assert client.post(f'/remediations/{rid}/propose-patch').status_code==409


def BAD_findings():
    from aegis.checks import analyze
    return analyze('https://example.test',BAD)


def test_failed_fix_reopens_original_and_notifies(client,mail,monkeypatch):
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    tid=applied(client,rid);age_jobs();jid=approve(client,tid,auth);worker.assess(jid)
    data=client.get(f'/organizations/{org}/intelligence').json()
    assert data['retests'][0]['status']=='failed_verification'
    assert 'header.csp' in data['retests'][0]['comparison']['unresolved']
    with Session() as db:assert db.get(Finding,fid).status=='reopened'
    assert any(n['kind']=='remediation_retest' for n in data['notifications'])
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409


def test_regression_and_rule_approval_gates(client,mail,monkeypatch):
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    assert client.post('/admin/intelligence/rules/remote.exploit/validate').status_code==422
    assert client.post('/admin/intelligence/rules/header.referrer/approve').status_code==409
    assert client.post('/admin/intelligence/rules/header.referrer/validate').json()['enabled'] is False
    assert client.post('/admin/intelligence/rules/header.referrer/approve').json()['enabled'] is True
    tid=applied(client,rid);age_jobs();jid=approve(client,tid,auth)
    monkeypatch.setattr(worker,'fetch',lambda o:GOOD);worker.assess(jid)
    r=client.get(f'/organizations/{org}/intelligence').json()['retests'][0]
    assert r['comparison']['new']==['header.referrer']
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409


def test_unsupported_old_findings_and_missing_cookies_stay_unverified(client,mail,monkeypatch):
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    with Session() as db:
        db.add(Finding(org_id=org,asset_id=asset,job_id=db.get(Finding,fid).job_id,rule='manual.unsupported',title='Manual fixture observation',severity='low',confidence='low',evidence='Controlled historical fixture',remediation='Human validation required'));db.commit()
    tid=applied(client,rid);age_jobs();jid=approve(client,tid,auth)
    no_cookie=Observation(200,[h for h in GOOD.headers if h[0]!='Set-Cookie'],b'',GOOD.tls)
    monkeypatch.setattr(worker,'fetch',lambda o:no_cookie);worker.assess(jid)
    data=client.get(f'/organizations/{org}/intelligence').json()['retests'][0]
    assert {x['rule'] for x in data['comparison']['unverified']}=={'manual.unsupported','cookie.secure','cookie.httponly'}
    with Session() as db:
        assert db.scalar(select(Finding).where(Finding.rule=='manual.unsupported')).status=='open'
        assert db.scalar(select(Finding).where(Finding.rule=='cookie.secure')).status=='open'
    assert client.patch(f'/remediations/{rid}/task',json={'status':'closed'}).status_code==409


def test_failed_retest_has_no_verified_fix(client,mail,monkeypatch):
    org,asset,auth,rid,fid=setup_fix(client,mail,monkeypatch)
    tid=applied(client,rid);age_jobs();jid=approve(client,tid,auth)
    def timeout(o):raise TimeoutError()
    monkeypatch.setattr(worker,'fetch',timeout);worker.assess(jid)
    assert client.get(f'/organizations/{org}/intelligence').json()['retests'][0]['status']=='unverified'
    assert client.get(f'/assessments/{jid}/report').status_code==404


def test_scheduler_slots_dedup_expiry_and_revocation(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(monitoring.dispatch_outbox,'delay',lambda:None)
    r=client.post(f'/assets/{asset}/schedule',json={'cadence':'weekly','accepted':True,'consent_days':30,'reverify':True});assert r.status_code==200
    assert len(monitoring.monitor_tick())==1
    assert monitoring.monitor_tick()==[]
    with Session() as db:
        schedule=db.get(AssessmentSchedule,r.json()['id']);schedule.next_due=0;db.get(Authorization,schedule.authorization_id).expires=0;db.commit()
    assert monitoring.monitor_tick()==[]
    data=client.get(f'/organizations/{org}/intelligence').json()
    # A revoked/expired authorization must never appear to permit recurring scans.
    assert data['schedules'][0]['status']=='blocked_no_current_consent'
    assert data['schedules'][0]['authorization_active'] is False
    assert any(n['kind']=='schedule_blocked' for n in data['notifications'])
    assert client.delete('/schedules/'+r.json()['id']).status_code==200
    assert monitoring.monitor_tick()==[]


def test_schedule_reverification_requires_still_published_proof(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(monitoring.dispatch_outbox,'delay',lambda:None)
    sid=client.post(f'/assets/{asset}/schedule',json={'cadence':'daily','accepted':True,'reverify':True}).json()['id']
    with Session() as db:db.get(Asset,asset).verified_until=0;db.commit()
    monkeypatch.setattr(verification,'verify',lambda *a:False)
    assert monitoring.monitor_tick()==[]
    with Session() as db:db.get(AssessmentSchedule,sid).next_due=0;db.commit()
    monkeypatch.setattr(verification,'verify',lambda *a:True)
    assert len(monitoring.monitor_tick())==1


def test_outbox_retries_without_duplicate_assessment(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(monitoring.dispatch_outbox,'delay',lambda:None)
    client.post(f'/assets/{asset}/schedule',json={'cadence':'daily','accepted':True})
    jobs=monitoring.monitor_tick();assert len(jobs)==1
    def down(**kwargs):raise ConnectionError()
    monkeypatch.setattr(worker.assess,'apply_async',down)
    monitoring.dispatch_outbox()
    with Session() as db:
        row=db.scalar(select(QueueOutbox));assert not row.dispatched and row.attempts==1;row.next_attempt=0;db.commit()
    sent=[];monkeypatch.setattr(worker.assess,'apply_async',lambda **kw:sent.append(kw))
    monitoring.dispatch_outbox();monitoring.dispatch_outbox()
    assert len(sent)==1 and sent[0]['args']==jobs


def test_intelligence_periodic_dispatch_once_per_tick(monkeypatch):
    sent=[];monkeypatch.setattr(monitoring.sync_intelligence,'apply_async',lambda **kw:sent.append(kw))
    assert len(monitoring.intelligence_tick())==4
    assert monitoring.intelligence_tick()==[]
    assert len(sent)==4
    with Session() as db:
        s=db.get(IntelligenceSource,'github');s.next_due=0;s.enabled=False;db.commit()
    assert monitoring.intelligence_tick()==[]

def test_recurring_explicit_paths_preserve_scope(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(monitoring.dispatch_outbox,'delay',lambda:None)
    response=client.post(f'/assets/{asset}/schedule',json={'cadence':'weekly','accepted':True,'paths':['/','/help']})
    assert response.status_code==200,response.text
    assert response.json()['scope']['paths']==['/','/help']
    jobs=monitoring.monitor_tick();assert len(jobs)==1
    with Session() as db:
        scope=db.get(Authorization,db.get(Job,jobs[0]).authorization_id).scope
        assert scope['request_limit']==2 and scope['type']=='explicit-path-response'
    invalid=client.post(f'/assets/{asset}/schedule',json={'cadence':'daily','accepted':True,'paths':['//external']})
    assert invalid.status_code==422
