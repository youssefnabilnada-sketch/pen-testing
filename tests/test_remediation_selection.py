from sqlalchemy import select
from conftest import signup
from test_assessment import authorized,launch,BAD
from aegis import worker
from aegis.db import Session
from aegis.models import Finding,Membership


def test_severity_selection_exclusions_reuse_and_tenants(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda origin:BAD);worker.assess(launch(client,asset,auth))
    with Session() as db:
        fs=db.scalars(select(Finding).order_by(Finding.id)).all()
        fs[0].severity='critical';fs[1].severity='high';fs[2].severity='critical';fs[2].status='accepted_risk'
        fs[3].severity='critical';fs[3].status='false_positive';fs[4].severity='critical';fs[4].status='resolved'
        excluded=fs[2].id;db.commit()
    path=f'/assets/{asset}/request-remediation'
    first=client.post(path,json={'selection':'critical'}).json()
    assert first['count']==1 and first['created']==1 and first['reused']==0 and first['applied'] is False
    second=client.post(path,json={'selection':'critical_high'}).json()
    assert second['count']==2 and second['created']==1 and second['reused']==1
    third=client.post(path,json={'selection':'all'}).json()
    assert third['count']==3 and third['created']==1 and third['reused']==2
    assert client.post(path).json()['created']==0
    assert client.post(path,json={'selection':'anything'}).status_code==422
    assert client.post('/remediations',json={'finding_id':excluded}).status_code==409
    with Session() as db:
        membership=db.scalar(select(Membership).where(Membership.org_id==org));membership.role='viewer';db.commit()
    assert client.post(path,json={'selection':'all'}).status_code==403
    client.post('/auth/logout');signup(client,mail,'other-selection@example.test')
    assert client.post(path).status_code==403


def test_empty_selection_does_not_claim_request_created(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    data=client.post(f'/assets/{asset}/request-remediation',json={'selection':'critical'}).json()
    assert data['count']==0 and data['created']==0 and data['applied'] is False
    assert 'No eligible findings' in data['message']

def test_remediation_pagination_beyond_100_and_isolation(client,mail,monkeypatch):
    from aegis.models import Remediation
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda origin:BAD);worker.assess(launch(client,asset,auth))
    with Session() as db:
        fid=db.scalar(select(Finding.id))
        for i in range(105):db.add(Remediation(org_id=org,finding_id=fid,status='closed',estimate='Historical fixture',created=float(i)))
        db.commit()
    path=f'/organizations/{org}/remediation-page'
    first=client.get(path+'?limit=100').json();last=client.get(path+'?offset=100').json()
    assert first['total']==105 and len(first['items'])==100 and len(last['items'])==5
    assert not {r['id'] for r in first['items']}&{r['id'] for r in last['items']}
    assert all(r['asset_id']==asset and r['finding_title'] for r in last['items'])
    assert client.get(path+'?status=requested').json()['total']==0
    for q in ('limit=101','offset=-1','status=paid'):
        assert client.get(path+'?'+q).status_code==422
    client.post('/auth/logout');signup(client,mail,'other-page@example.test')
    assert client.get(path).status_code==403
