import pytest
from aegis.runtime import validate_runtime
from aegis import auth

def configure(monkeypatch):
    for key,value in {'AEGIS_ENV':'production','DATABASE_URL':'postgresql+psycopg://aegis:dummy@127.0.0.1/aegis',
       'REDIS_URL':'redis://127.0.0.1:6379/0','WEB_ORIGIN':'https://security.example.test',
       'COOKIE_SECURE':'true','LOCAL_FIXTURE_MODE':'false','PAYMENTS_ENABLED':'false','BILLING_MODE':'disabled',
       'FIREBASE_AUTH_ENABLED':'true','FIREBASE_PROJECT_ID':'aegis-test',
       'FIREBASE_WEB_API_KEY':'public-fixture','FIREBASE_WEB_APP_ID':'fixture-app',
       'SMTP_TLS':'starttls','SMTP_HOST':'smtp.example.test','MAIL_FROM':'security@example.test',
       'MFA_ENCRYPTION_KEY':'ZJ01PwF8FT8O778kbGS12YyoMddJxNqicR0lX-_bUHw='}.items():
        monkeypatch.setenv(key,value)
    monkeypatch.delenv('TESTING',raising=False)
    monkeypatch.setenv('PADDLE_ENABLED','false')
    monkeypatch.setenv('INSTAPAY_ENABLED','false')

@pytest.mark.parametrize('key,value',[
    ('DATABASE_URL','sqlite:///dev.db'),('COOKIE_SECURE','false'),('LOCAL_FIXTURE_MODE','true'),
    ('WEB_ORIGIN','http://localhost:3000'),('WEB_ORIGIN','https://security.example.test/?token=oops'),
    ('WEB_ORIGIN','https://security.example.test/#fragment'),
    ('WEB_ORIGIN','https://user:password@security.example.test'),
    ('TESTING','1'),('TESTING','true'),('PAYMENTS_ENABLED','true'),
    ('PADDLE_ENABLED','true'),('INSTAPAY_ENABLED','true'),
    ('REDIS_URL',''),('REDIS_URL','https://redis.example.test/'),
    ('REDIS_URL','redis:///0'),('REDIS_URL','redis://host:invalid/0'),
    ('FIREBASE_AUTH_ENABLED','false'),('FIREBASE_PROJECT_ID',''),
    ('SMTP_TLS','none'),('SMTP_HOST',''),('MAIL_FROM',''),
    ('MFA_ENCRYPTION_KEY','not-a-valid-key')])
def test_public_runtime_rejects_development_settings(monkeypatch,key,value):
    configure(monkeypatch);monkeypatch.setenv(key,value)
    with pytest.raises(RuntimeError):validate_runtime()

def test_production_settings_validate_without_claiming_connection(monkeypatch):
    configure(monkeypatch);validate_runtime()

def test_email_encryption_and_redaction(monkeypatch):
    configure(monkeypatch);monkeypatch.setenv('SMTP_TLS','none')
    with pytest.raises(OSError,match='Encrypted'):auth.smtp_connection()
    monkeypatch.setenv('SMTP_TLS','starttls')
    monkeypatch.setenv('SMTP_USERNAME','fixture-user');monkeypatch.setenv('SMTP_PASSWORD','private-test-value')
    events=[]
    class SMTP:
        def __init__(self,*args,**kwargs):events.append('connect')
        def ehlo(self):events.append('ehlo')
        def starttls(self,context):assert context.check_hostname;events.append('tls')
        def login(self,*args):events.append('login');raise ValueError('private-test-value')
        def close(self):events.append('closed')
    monkeypatch.setattr(auth.smtplib,'SMTP',SMTP)
    with pytest.raises(OSError) as err:auth.smtp_connection()
    assert 'private-test-value' not in str(err.value)
    assert events==['connect','ehlo','tls','ehlo','login','closed']
