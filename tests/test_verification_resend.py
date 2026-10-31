"""Public verification resend: safe recovery for expired signup tokens."""
import time
from sqlalchemy import select
from aegis.db import Session
from aegis.models import EmailToken, User
from aegis import main

ACCOUNT='pilot@example.test'
PASSWORD='Long-password123!'


def _register(client, mail):
    response=client.post('/auth/register',json={'email':ACCOUNT,'password':PASSWORD})
    assert response.status_code==201,response.text
    assert len(mail)==1
    return mail[-1][1]


def _expire_token():
    with Session() as db:
        row=db.scalar(select(EmailToken).where(EmailToken.purpose=='verify'))
        assert row is not None
        row.expires=time.time()-1
        db.commit()


def test_expired_signup_can_resend_without_creating_duplicate_account(client,mail):
    previous=_register(client,mail)
    _expire_token()
    result=client.post('/auth/resend-verification',json={'email':ACCOUNT})
    assert result.status_code==202
    assert len(mail)==2 and mail[-1][1]!=previous
    assert client.post('/auth/verify',json={'token':previous}).status_code==400
    assert client.post('/auth/verify',json={'token':mail[-1][1]}).status_code==200
    with Session() as db:
        assert len(db.scalars(select(User)).all())==1
        assert db.scalar(select(User)).verified is True


def test_resend_cooldown_does_not_revoke_recent_valid_code(client,mail):
    old=_register(client,mail)
    response=client.post('/auth/resend-verification',json={'email':ACCOUNT})
    assert response.status_code==202
    assert len(mail)==1
    assert client.post('/auth/verify',json={'token':old}).status_code==200


def test_unknown_or_verified_address_returns_indistinguishable_response(client,mail):
    missing=client.post('/auth/resend-verification',json={'email':'unknown@example.test'})
    token=_register(client,mail)
    assert client.post('/auth/verify',json={'token':token}).status_code==200
    verified=client.post('/auth/resend-verification',json={'email':ACCOUNT})
    assert missing.status_code==verified.status_code==202
    assert missing.json()==verified.json()
    assert len(mail)==1


def test_email_failure_rolls_back_and_does_not_reveal_account(client,mail,monkeypatch):
    old=_register(client,mail)
    _expire_token()
    def failing_email(*args):
        raise OSError('fixture SMTP transport unavailable')
    monkeypatch.setattr(main,'send_token',failing_email)
    failed=client.post('/auth/resend-verification',json={'email':ACCOUNT})
    missing=client.post('/auth/resend-verification',json={'email':'missing@example.test'})
    assert failed.status_code==missing.status_code==202
    assert failed.json()==missing.json()
    assert len(mail)==1
    with Session() as db:
        row=db.scalar(select(EmailToken).where(EmailToken.purpose=='verify'))
        assert row is not None and row.digest==main.digest(old)
        assert row.expires<time.time()
