"""Opt-in local Mailpit delivery and one-time account email tests."""
import os
import re
import time
import uuid
import httpx
import pytest

@pytest.mark.skipif(os.getenv('AEGIS_TEST_MAILPIT')!='1', reason='Local Mailpit opt-in')
def test_mailpit_verification_and_recovery(client, monkeypatch):
    from aegis import main, auth
    monkeypatch.setattr(main,'send_token',auth.send_token)
    for key,value in {'SMTP_HOST':'127.0.0.1','SMTP_PORT':'1025','SMTP_TLS':'none','WEB_ORIGIN':'http://localhost:3000'}.items():
        monkeypatch.setenv(key,value)
    monkeypatch.delenv('SMTP_USERNAME',raising=False)
    email='mailpit-'+uuid.uuid4().hex+'@example.test'
    password='Controlled-Local-Email-123!'
    assert client.post('/auth/register',json={'email':email,'password':password}).status_code==201
    def token(purpose):
        until=time.monotonic()+5
        while time.monotonic()<until:
            data=httpx.get('http://127.0.0.1:8025/api/v1/messages',timeout=2,trust_env=False).json()
            for message in data['messages']:
                if any(x['Address']==email for x in message['To']) and message['Subject']=='AEGIS: '+purpose:
                    body=httpx.get('http://127.0.0.1:8025/api/v1/message/'+message['ID'],timeout=2,trust_env=False).json()['Text']
                    return re.search(r'#'+purpose+r'=([A-Za-z0-9_-]+)',body).group(1)
            time.sleep(.1)
        raise AssertionError('Expected message did not reach local Mailpit.')
    verify=token('verify')
    assert client.post('/auth/verify',json={'token':verify}).status_code==200
    assert client.post('/auth/verify',json={'token':verify}).status_code==400
    assert client.post('/auth/reset-request',json={'email':email}).status_code==200
    reset=token('reset')
    new_password='Controlled-Recovered-Password-456!'
    assert client.post('/auth/reset',json={'token':reset,'password':new_password}).status_code==200
    assert client.post('/auth/reset',json={'token':reset,'password':new_password}).status_code==400
    assert client.post('/auth/login',json={'email':email,'password':new_password}).status_code==200
