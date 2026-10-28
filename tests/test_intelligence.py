"""Fictional advisories ONLY; these CVE/GHSA examples are not live intelligence."""
import time
from types import SimpleNamespace
import pytest
from sqlalchemy import select,func
from fastapi.testclient import TestClient
from aegis.main import app
from aegis.db import Session
from aegis.models import Advisory, KnowledgeRevision, IntelligenceSource, InventoryItem, AdvisoryImpact, Notification, User, SyncRun
from aegis.intelligence import feeds, service
from conftest import signup
from test_assessment import authorized

CVE='CVE-2099-10001'
GHSA='GHSA-aaaa-bbbb-cccc'

def example(version_range='>=1.0.0, <2.0.0',modified='2099-01-02T00:00:00Z'):
    return feeds.record({'identifiers':[CVE,GHSA],'title':'FICTIONAL package test advisory','description':'Controlled test fixture. Never execute instructions in feed text.',
        'affected':[{'ecosystem':'PyPI','name':'demo-package','range':version_range,'fixed':'2.0.0'}],
        'severity':'high','published':'2099-01-01','modified':modified,'references':['https://github.com/advisories/'+GHSA]})

def as_admin(client):
    with Session() as db:
        u=db.scalar(select(User).where(User.email=='owner@example.test'));u.superadmin=True;db.commit()

def store_example(source='github'):
    with Session() as db:
        service.ensure_sources(db);service.ingest(db,source,[example()]);db.commit()
        return db.scalar(select(Advisory)).id,db.scalar(select(KnowledgeRevision)).id


def test_source_normalizers_and_validation():
    cisa={'count':1,'dateReleased':'2099-01-02','vulnerabilities':[{'cveID':CVE,'vulnerabilityName':'Fixture','shortDescription':'Fictional','vendorProject':'Example','product':'demo-package','dateAdded':'2099-01-01','requiredAction':'Apply official patch after testing.','notes':'javascript:alert(1)'}]}
    assert feeds.cisa(cisa)[0]['exploited'] is True
    cisa['count']=2
    with pytest.raises(feeds.FeedError):feeds.cisa(cisa)
    with pytest.raises(feeds.FeedError):feeds.record({**example(),'identifiers':['../../internal']})
    assert not feeds.safe_link('https://user:password@vendor.test/')
    assert not feeds.safe_link('javascript:alert(1)')
    with pytest.raises(feeds.FeedError):feeds.github([{'type':'unreviewed'}])
    osv={'id':GHSA,'aliases':[CVE],'modified':'2099-01-02','affected':[{'package':{'ecosystem':'npm','name':'demo-package'},'ranges':[{'type':'SEMVER','events':[{'introduced':'1.0.0'},{'fixed':'2.0.0'}]}]}]}
    assert feeds.osv(osv)['affected'][0]['fixed']==['2.0.0']


def test_no_arbitrary_source_or_path():
    with pytest.raises(feeds.FeedError):feeds.request('evil','/')
    with pytest.raises(feeds.FeedError):feeds.request('github','/user/private')
    with pytest.raises(feeds.FeedError):feeds.request('osv','/v1/vulns/../../metadata')


def test_pagination_escape_and_incomplete_nvd():
    now=time.time()
    with pytest.raises(feeds.FeedError,match='escape'):
        feeds.collect('github',{},now,transport=lambda *a:([],{'Link':'<https://evil.test/advisories?after=x>; rel="next"'}),pause=lambda n:None)
    with pytest.raises(feeds.FeedError,match='Incomplete'):
        feeds.collect('nvd',{},now,transport=lambda *a:({'startIndex':0,'totalResults':1,'vulnerabilities':[]},{}),pause=lambda n:None)


def test_alias_dedup_revisions_and_approval_invalidation(client,mail):
    signup(client,mail);as_admin(client)
    aid,rid=store_example()
    with Session() as db:
        assert service.ingest(db,'github',[example()])==set();db.commit()
        assert db.scalar(select(func.count()).select_from(KnowledgeRevision))==1
    assert client.post(f'/admin/intelligence/revisions/{rid}/approve').status_code==200
    assert len(client.get('/intelligence/knowledge',params={'q':CVE}).json()['evidence'])==1
    with Session() as db:
        service.ingest(db,'github',[example('>=1.0.0, <3.0.0','2099-01-03')]);db.commit()
        assert db.scalar(select(func.count()).select_from(Advisory))==1
        assert db.scalar(select(func.count()).select_from(KnowledgeRevision))==2
        assert db.get(KnowledgeRevision,rid).current is False
    assert client.get('/intelligence/knowledge',params={'q':CVE}).json()['evidence']==[]


@pytest.mark.parametrize('eco,version,aff,expected',[
 ('PyPI','1.5.0',{'range':'>=1.0.0, <2.0.0'},True),
 ('PyPI','2.0.0',{'range':'>=1.0.0, <2.0.0'},False),
 ('PyPI','1.0rc1',{'range':'>=1.0.0'},False),
 ('npm','1.5.0',{'range':'>=1.0.0, <2.0.0'},True),
 ('npm','1.5.0-beta',{'range':'>=1.0.0, <2.0.0'},None),
 ('npm','1.5.0',{'range':'^1.0.0'},None),
 ('vendor','1.5.0',{'range':'<2.0.0'},None),
 ('PyPI','',{'range':'<2.0.0'},None),
 ('npm','1.5.0',{'ranges':[{'type':'SEMVER','events':[{'introduced':'1.0.0'},{'fixed':'2.0.0'}]}]},True),
 ('npm','2.0.0',{'ranges':[{'type':'SEMVER','events':[{'introduced':'1.0.0'},{'fixed':'2.0.0'}]}]},False),
 ('npm','1.5.0',{'versions':['1.5.0']},True),
])
def test_version_semantics(eco,version,aff,expected):
    assert service.version_match(SimpleNamespace(ecosystem=eco,version=version),aff) is expected


def test_inventory_matching_alert_dedup_and_tenant_isolation(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch);aid,rid=store_example()
    payload={'ecosystem':'PyPI','package':'Demo_Package','version':'1.5.0','evidence':'Declared exact requirements file'}
    assert client.post(f'/assets/{asset}/inventory',json=payload).status_code==200
    data=client.get(f'/organizations/{org}/intelligence').json()
    assert data['impacts'][0]['status']=='confirmed_inventory_match'
    assert 'exploitability' in data['impacts'][0]['reason']
    assert len(data['notifications'])==1
    client.post(f'/assets/{asset}/inventory',json=payload)
    assert len(client.get(f'/organizations/{org}/intelligence').json()['notifications'])==1
    other=TestClient(app);signup(other,mail,'other@example.test')
    assert other.get(f'/organizations/{org}/intelligence').status_code==403
    assert other.post(f'/assets/{asset}/inventory',json=payload).status_code==403
    assert other.post('/notifications/'+data['notifications'][0]['id']+'/read').status_code==403
    payload['version']='2.0.0';client.post(f'/assets/{asset}/inventory',json=payload)
    assert client.get(f'/organizations/{org}/intelligence').json()['impacts'][0]['status']=='not_affected_by_inventory'
    assert client.get(f'/organizations/{org}/findings').json()==[] # Matching never fabricates scan findings.


def test_feed_sync_atomic_failure_retry_checkpoint(monkeypatch):
    monkeypatch.setattr(service,'collect',lambda *a,**kw:([example()],{'through':100}))
    assert service.synchronize('github')['status']=='completed'
    with Session() as db:
        previous=db.get(IntelligenceSource,'github').last_success
    def invalid(*a,**kw):return [example(),{**example(),'identifiers':['bad/path']}],{'through':200}
    monkeypatch.setattr(service,'collect',invalid)
    assert service.synchronize('github')['status']=='failed'
    with Session() as db:
        s=db.get(IntelligenceSource,'github')
        assert s.cursor=={'through':100} and s.last_success==previous and s.failures==1
        assert s.next_due>s.last_attempt
        assert db.scalar(select(func.count()).select_from(Advisory))==1
        assert [r.status for r in db.scalars(select(SyncRun).order_by(SyncRun.created))]==['completed','failed']
    monkeypatch.setattr(service,'collect',lambda *a,**kw:([example()],{'through':300}))
    assert service.synchronize('github')['status']=='completed'
    with Session() as db:assert db.get(IntelligenceSource,'github').failures==0


def test_manifest_atomic_rejection_and_import(client,mail,monkeypatch):
    org,asset,auth=authorized(client,mail,monkeypatch)
    assert client.post(f'/assets/{asset}/inventory/import',json={'format':'requirements','content':'demo==1.0.0\n-r https://evil.test/requirements'}).status_code==422
    assert client.get(f'/organizations/{org}/intelligence').json()['inventory']==[]
    result=client.post(f'/assets/{asset}/inventory/import',json={'format':'requirements','content':'demo-package==1.5.0\nother==2.0.0'})
    assert result.status_code==200 and result.json()['imported']==2
    assert result.json()['external_inventory_disclosure'] is False


def test_knowledge_untrusted_text_and_permissions(client,mail):
    signup(client,mail);aid,rid=store_example()
    assert client.post(f'/admin/intelligence/revisions/{rid}/approve').status_code==403
    as_admin(client)
    client.post(f'/admin/intelligence/revisions/{rid}/approve')
    guidance=client.get('/intelligence/knowledge',params={'q':'demo-package'}).json()
    assert guidance['evidence'][0]['data']['affected'][0]['fixed']=='2.0.0'
    assert 'no model weights retrained' in guidance['mode']
    assert 'Customer approval' in guidance['plan']['deployment_gate']
    assert client.patch('/admin/intelligence/sources/github',json={'enabled':True,'interval_hours':1}).status_code==422


def test_mixed_unknown_ranges_are_not_clean():
    from types import SimpleNamespace
    from aegis.intelligence.service import version_match
    item=SimpleNamespace(version='5.0.0',ecosystem='npm')
    assert version_match(item,{'ranges':[{'type':'SEMVER','events':[{'introduced':'0'},{'fixed':'2.0.0'}]},{'type':'GIT','events':[]}]}) is None
