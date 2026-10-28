import os,time,uuid
import pytest
from sqlalchemy import select
from aegis.db import Session
from aegis.models import EmailDelivery,Notification
from aegis import email_alerts as email
from aegis.intelligence.service import notify
from conftest import signup

def alert(org,key='one'):
    with Session() as db:
        notify(db,org,'health_change',key,'Controlled health incident','Private evidence stays in the dashboard','fixture');db.commit()
        return db.scalar(select(EmailDelivery.id).order_by(EmailDelivery.created.desc()).limit(1))

def test_opt_in_retry_revoke_and_dedup(client,mail,monkeypatch):
    org=signup(client,mail)
    assert alert(org) is None
    client.put(f'/organizations/{org}/email-preferences',json={'enabled_kinds':['health_change']})
    did=alert(org,'two');assert did
    alert(org,'two')
    with Session() as db:assert len(list(db.scalars(select(EmailDelivery))))==1
    def fail():raise OSError('private smtp detail')
    monkeypatch.setattr(email,'smtp_connection',fail)
    email.send_alert(did)
    history=client.get(f'/organizations/{org}/email-history').json()
    assert history[0]['status']=='pending' and history[0]['attempts']==1
    assert 'private smtp detail' not in str(history)
    client.put(f'/organizations/{org}/email-preferences',json={'enabled_kinds':[]})
    with Session() as db:db.get(EmailDelivery,did).next_due=0;db.commit()
    email.send_alert(did)
    assert client.get(f'/organizations/{org}/email-history').json()[0]['status']=='cancelled'

@pytest.mark.skipif(os.getenv('AEGIS_TEST_MAILPIT')!='1',reason='Requires local Mailpit')
def test_real_mailpit_guardian_delivery(client,mail,monkeypatch):
    import httpx
    address='guardian-'+uuid.uuid4().hex+'@example.test'
    org=signup(client,mail,address)
    for k,v in {'SMTP_HOST':'127.0.0.1','SMTP_PORT':'1025','SMTP_TLS':'none'}.items():monkeypatch.setenv(k,v)
    monkeypatch.delenv('SMTP_USERNAME',raising=False)
    client.put(f'/organizations/{org}/email-preferences',json={'enabled_kinds':['health_change']})
    did=alert(org);email.send_alert(did);email.send_alert(did)
    assert client.get(f'/organizations/{org}/email-history').json()[0]['status']=='smtp_accepted'
    messages=httpx.get('http://127.0.0.1:8025/api/v1/messages',trust_env=False,timeout=3).json()['messages']
    matches=[m for m in messages if any(x['Address']==address for x in m['To'])]
    assert len(matches)==1
    body=httpx.get('http://127.0.0.1:8025/api/v1/message/'+matches[0]['ID'],trust_env=False,timeout=3).json()['Text']
    assert 'Controlled health incident' in body and 'Private evidence' not in body


def test_final_attempt_worker_crash_is_terminal_and_not_resent(client,mail,monkeypatch):
    org=signup(client,mail)
    client.put(f'/organizations/{org}/email-preferences',json={'enabled_kinds':['health_change']})
    did=alert(org)
    with Session() as db:
        d=db.get(EmailDelivery,did);d.status='sending';d.attempts=5;d.next_due=time.time()+120;db.commit()
    sent=[];monkeypatch.setattr(email.send_alert,'delay',lambda d:sent.append(d))
    email.tick()
    with Session() as db:
        assert db.get(EmailDelivery,did).status=='sending'
        db.get(EmailDelivery,did).next_due=0;db.commit()
    email.tick();email.send_alert(did)
    with Session() as db:
        d=db.get(EmailDelivery,did)
        assert d.status=='failed' and d.attempts==5 and 'unknown' in d.error
    assert sent==[]


def test_dispatch_failure_preserves_batch_and_retryability(client,mail,monkeypatch):
    org=signup(client,mail)
    client.put(f'/organizations/{org}/email-preferences',json={'enabled_kinds':['health_change']})
    first=alert(org,'first');second=alert(org,'second');attempted=[]
    def dispatch(did):
        attempted.append(did)
        if did==first:raise OSError('broker unavailable')
    monkeypatch.setattr(email.send_alert,'delay',dispatch)
    assert email.tick()==1 and attempted==[first,second]
    with Session() as db:
        assert db.get(EmailDelivery,first).status=='pending'
        assert db.get(EmailDelivery,first).attempts==0
    monkeypatch.setattr(email.send_alert,'delay',lambda did:None)
    assert email.tick()==2


def test_expired_claim_retries_but_live_claim_does_not(client,mail,monkeypatch):
    org=signup(client,mail)
    client.put(f'/organizations/{org}/email-preferences',json={'enabled_kinds':['health_change']})
    did=alert(org);messages=[]
    class SMTP:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def send_message(self,msg):messages.append(msg);return {}
    monkeypatch.setattr(email,'smtp_connection',SMTP)
    with Session() as db:
        d=db.get(EmailDelivery,did);d.status='sending';d.attempts=1;d.next_due=time.time()+120;db.commit()
    email.send_alert(did);assert not messages
    with Session() as db:db.get(EmailDelivery,did).next_due=0;db.commit()
    email.send_alert(did);email.send_alert(did)
    assert len(messages)==1
    with Session() as db:
        d=db.get(EmailDelivery,did);assert d.status=='smtp_accepted' and d.attempts==2

from test_smtp_delivery import smtp_inbox


def test_guardian_actual_loopback_smtp_acceptance(client,mail,smtp_inbox):
    org=signup(client,mail)
    client.put(f'/organizations/{org}/email-preferences',json={'enabled_kinds':['health_change']})
    did=alert(org)
    email.send_alert(did);email.send_alert(did)
    assert len(smtp_inbox)==1
    assert smtp_inbox[0]['Message-ID']==f'<aegis-alert-{did}@notifications.aegis>'
    body=smtp_inbox[0].get_content()
    assert 'Controlled health incident' in body and 'Private evidence' not in body
    assert client.get(f'/organizations/{org}/email-history').json()[0]['status']=='smtp_accepted'
