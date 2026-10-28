import pytest
from fastapi.testclient import TestClient
from aegis.main import app
from aegis.smartverify import recommend,Capabilities
from conftest import signup
from test_onboarding import setup
@pytest.mark.parametrize('origin,options,method,platform',[
 ('https://a.vercel.app',{},'file','vercel'),
 ('https://vercel.app.attacker.test',{},'dns','other'),
 ('https://owned.test',{'platform':'wordpress'},'meta','wordpress'),
 ('https://owned.test',{'dns_access':True},'dns','other'),
 ('https://owned.test',{'html_access':True},'meta','other'),
 ('https://owned.test',{'repository_access':True},'file','other'),
])
def test_capability_recommendations(origin,options,method,platform):
    result=recommend(origin,Capabilities(**options))
    assert result['method']==method and result['platform']==platform
    assert not result['automatic_connection']

def test_download_history_wordpress_and_isolation(client,mail,monkeypatch):
    asset=setup(client,mail,monkeypatch)
    challenge=client.post(f'/assets/{asset}/challenge',json={'method':'file'}).json()
    download=f'/assets/{asset}/challenge/{challenge["id"]}/file'
    r=client.get(download)
    assert r.status_code==200 and r.text==challenge['token']
    assert r.headers['cache-control']=='no-store'
    history=client.get(f'/assets/{asset}/verification-history').json()
    assert history[0]['state']=='pending' and 'token' not in history[0]
    meta=client.post(f'/assets/{asset}/challenge',json={'method':'meta'}).json()
    assert meta['wordpress']=={'origin':'https://example.test','token':meta['token'],'expires':meta['expires']}
    other=TestClient(app);signup(other,mail,'smartverify-outsider@example.test')
    assert other.get(download).status_code==403
    assert other.get(f'/assets/{asset}/verification-history').status_code==403
    assert other.post(f'/assets/{asset}/verification-recommendation',json={}).status_code==403
    client.post(f'/assets/{asset}/revoke')
    assert client.get(download).status_code==400
    assert client.post(f'/assets/{asset}/authorize',json={'accepted':True}).status_code==403


def test_revoked_challenge_during_verification_cannot_restore_ownership(client,mail,monkeypatch):
    from aegis.db import Session
    from aegis.models import Challenge
    asset=setup(client,mail,monkeypatch)
    c=client.post(f'/assets/{asset}/challenge',json={'method':'meta'}).json()
    def verify(*args):
        with Session() as db:db.get(Challenge,c['id']).consumed=True;db.commit()
        return True
    monkeypatch.setattr('aegis.verification.verify',verify)
    assert client.post(f'/assets/{asset}/verify/{c["id"]}').status_code==400
    assert client.post(f'/assets/{asset}/authorize',json={'accepted':True}).status_code==403
