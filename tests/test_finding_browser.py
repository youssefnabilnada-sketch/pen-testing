from conftest import signup
from test_assessment import authorized,launch,BAD
from aegis import worker
from aegis.db import Session
from aegis.models import Finding,FindingHistory
from sqlalchemy import select


def test_finding_pages_filters_history_and_isolation(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    monkeypatch.setattr(worker,'fetch',lambda o:BAD);jid=launch(client,asset,auth);worker.assess(jid)
    with Session() as db:
        for i in range(28):db.add(Finding(org_id=org,asset_id=asset,job_id=jid,rule=f'fixture.{i}',title=f'Fixture {i}',severity='low',confidence='high',evidence='Local fixture',remediation='Review fixture'))
        db.commit()
    base=f'/organizations/{org}/finding-page'
    first=client.get(base+'?limit=25').json();second=client.get(base+'?offset=25').json()
    assert first['total']>25 and len(first['items'])==25 and len(second['items'])==first['total']-25
    assert not {r['id'] for r in first['items']}&{r['id'] for r in second['items']}
    assert client.get(base+'?q=fixture.27').json()['total']==1
    assert client.get(base+'?q=%25').json()['total']==0
    assert client.get(base+'?severity=critical').json()['total']==0
    ordered=client.get(base+'?sort=severity').json()['items'];assert ordered[0]['severity']=='medium'
    fid=client.get(base+'?q=fixture.27').json()['items'][0]['id']
    assert client.patch('/findings/'+fid,json={'status':'under_review'}).status_code==200
    history=client.get('/findings/'+fid+'/history').json()
    assert history['total']==1 and history['items'][0]['status']=='under_review'
    assert client.get(base+'?status=under_review').json()['total']==1
    for invalid in ('limit=101','offset=-1','sort=sql','severity=urgent','status=secure'):
        assert client.get(base+'?'+invalid).status_code==422
    assert client.post('/remediations',json={'finding_id':fid}).status_code==201
    remediation=client.get(f'/organizations/{org}/remediations').json()[0]
    assert remediation['asset_id']==asset and remediation['finding_title']=='Fixture 27'
    client.post('/auth/logout');signup(client,mail,'other@example.test')
    assert client.get(base).status_code==403
    assert client.get('/findings/'+fid+'/history').status_code==403
