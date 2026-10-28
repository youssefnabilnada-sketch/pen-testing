from fastapi.testclient import TestClient
from sqlalchemy import select
from aegis.main import app
from aegis.db import Session
from aegis.models import User,Report
from aegis import worker
from conftest import signup
from test_assessment import authorized,launch,BAD

def test_crm_beta_is_single_use_and_scanning_not_authorized(client,mail):
    org=signup(client,mail)
    r=client.post(f'/organizations/{org}/crm-requests',json={'kind':'beta','message':'Please invite my team to private beta.','contact_consent':False})
    assert r.status_code==200;lead=r.json()['id']
    assert client.get('/admin/crm').status_code==403
    staff=TestClient(app);signup(staff,mail,'staff@example.test')
    with Session() as db:db.scalar(select(User).where(User.email=='staff@example.test')).superadmin=True;db.commit()
    invite=staff.post(f'/admin/crm/{lead}/beta-invitation').json()
    assert invite['message_sent'] is False
    assert staff.post('/crm/beta-accept',json={'token':invite['token']}).status_code==400
    accepted=client.post('/crm/beta-accept',json={'token':invite['token']})
    assert accepted.status_code==200 and accepted.json()['assessment_authorized'] is False
    assert client.post('/crm/beta-accept',json={'token':invite['token']}).status_code==400
    assert staff.get('/admin/crm').json()['conversion_rate']==1
    assert staff.get(f'/organizations/{org}/crm-requests').status_code==403

def test_evidence_seal_blocks_drift_and_cross_tenant_export(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda origin:BAD)
    jid=launch(client,asset,auth);worker.assess(jid)
    vault=client.get(f'/organizations/{org}/evidence-vault').json()
    row=vault['items'][0];assert row['integrity']=='verified'
    path=f'/evidence-vault/{row["id"]}/export'
    assert client.get(path).json()['integrity']=='verified'
    other=TestClient(app);signup(other,mail,'vault-other@example.test')
    assert other.get(path).status_code==403
    with Session() as db:
        r=db.get(Report,row['id']);r.snapshot={**r.snapshot,'status':'tampered'};db.commit()
    assert client.get(path).status_code==409
    assert client.get(f'/assessments/{jid}/report').status_code==409


def test_crm_consent_withdrawal_is_private_audited_and_blocks_followups(client,mail):
    from aegis.models import Lead
    org=signup(client,mail)
    lead=client.post(f'/organizations/{org}/crm-requests',json={'kind':'demo','message':'Please demonstrate the platform.','contact_consent':True}).json()['id']
    staff=TestClient(app);signup(staff,mail,'staff-consent@example.test')
    with Session() as db:db.scalar(select(User).where(User.email=='staff-consent@example.test')).superadmin=True;db.commit()
    update={'status':'demo_scheduled','note':'Customer requested a demonstration.','followup_at':1}
    assert staff.patch(f'/admin/crm/{lead}',json=update).status_code==200
    endpoint=f'/organizations/{org}/crm-requests/{lead}/withdraw-consent'
    assert staff.post(endpoint).status_code==403
    assert client.post(endpoint).json()=={'contact_consent':False,'message_sent':False}
    assert client.post(endpoint).status_code==200
    with Session() as db:
        r=db.get(Lead,lead)
        assert not r.contact_consent and r.followup_at is None
        assert len([h for h in r.history if h['note']=='Customer withdrew contact consent.'])==1
    assert staff.get('/admin/crm').json()['due_followups']==0
    assert staff.patch(f'/admin/crm/{lead}',json=update).status_code==409
    assert client.post(f'/organizations/{org}/crm-requests/missing/withdraw-consent').status_code==404


def test_evidence_legal_hold_is_audited_and_workspace_scoped(client,mail,monkeypatch):
    from aegis.models import EvidenceLegalHold
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda origin:BAD)
    jid=launch(client,asset,auth);worker.assess(jid)
    report=client.get(f'/organizations/{org}/evidence-vault').json()['items'][0]
    rid=report['id']
    assert report['legal_hold'] is False
    endpoint=f'/evidence-vault/{rid}/legal-hold'
    assert client.post(endpoint,json={'reason':'   '}).status_code==422
    assert client.post(endpoint,json={'reason':'Formal investigation pending review'}).status_code==200
    assert client.post(endpoint,json={'reason':'Duplicate legal hold'}).status_code==409
    assert client.get(f'/organizations/{org}/evidence-vault').json()['items'][0]['legal_hold'] is True
    other=TestClient(app);signup(other,mail,'evidence-other@example.test')
    assert other.get(f'/evidence-vault/{rid}/legal-holds').status_code==403
    assert other.post(endpoint,json={'reason':'Unauthorized request'}).status_code==403
    assert other.post(endpoint+'/release',json={'reason':'Unauthorized release'}).status_code==403
    assert client.post(endpoint+'/release',json={'reason':'Investigation has concluded'}).status_code==200
    assert client.get(f'/organizations/{org}/evidence-vault').json()['items'][0]['legal_hold'] is False
    assert len(client.get(f'/evidence-vault/{rid}/legal-holds').json()['items'])==1
    with Session() as db:
        rows=db.scalars(select(EvidenceLegalHold).where(EvidenceLegalHold.report_id==rid)).all()
        assert len(rows)==1 and rows[0].released_at is not None
        assert db.get(Report,rid) is not None
