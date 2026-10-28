from fastapi.testclient import TestClient
from sqlalchemy import select,func
from aegis.main import app
from aegis.db import Session
from aegis.models import Notification,NotificationRead
from conftest import signup

def test_personal_preferences_read_state_and_tenant_isolation(client,mail):
    org=signup(client,mail)
    peer=TestClient(app);signup(peer,mail,'peer@example.test')
    client.post(f'/organizations/{org}/members',json={'email':'peer@example.test','role':'viewer'})
    with Session() as db:
        a=Notification(org_id=org,kind='advisory_impact',dedupe_key='a',title='Advisory match',detail='Potential only',target='fixture')
        b=Notification(org_id=org,kind='assessment_failed',dedupe_key='b',title='Failed',detail='No conclusion',target='fixture')
        db.add_all([a,b]);db.commit();aid=a.id
    preferences=f'/organizations/{org}/notification-preferences'
    feed=f'/organizations/{org}/intelligence'
    assert len(client.get(preferences).json()['enabled_kinds'])==6
    assert len(client.get(feed).json()['notifications'])==2
    assert peer.put(preferences,json={'enabled_kinds':['assessment_failed']}).status_code==200
    assert len(peer.get(feed).json()['notifications'])==1
    assert len(client.get(feed).json()['notifications'])==2
    for _ in range(2):assert client.post(f'/notifications/{aid}/read').status_code==200
    assert next(n for n in client.get(feed).json()['notifications'] if n['id']==aid)['read'] is True
    peer.put(preferences,json={'enabled_kinds':['advisory_impact']})
    assert peer.get(feed).json()['notifications'][0]['read'] is False
    with Session() as db:assert db.scalar(select(func.count()).select_from(NotificationRead))==1
    outsider=TestClient(app);signup(outsider,mail,'outsider@example.test')
    assert outsider.get(preferences).status_code==403
    assert outsider.put(preferences,json={'enabled_kinds':[]}).status_code==403
    assert outsider.post(f'/notifications/{aid}/read').status_code==403
    assert client.put(preferences,json={'enabled_kinds':['invented']}).status_code==422
    assert client.put(preferences,json={'enabled_kinds':[]}).status_code==200
    assert client.get(feed).json()['notifications']==[]
