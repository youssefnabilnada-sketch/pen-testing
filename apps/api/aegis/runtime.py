"""Fail closed when a public deployment inherits development configuration."""
import os
from urllib.parse import urlsplit
from .db import connection_url

def validate_runtime(role=None):
    """Fail closed for production while keeping credentials limited to roles that use them.

    API handles identity/account email/MFA; notifier handles alert SMTP;
    scanners, intelligence and scheduler do not need those secrets.
    """
    if os.getenv('AEGIS_ENV')!='production':return
    role=role or os.getenv('AEGIS_SERVICE_ROLE','api')
    problems=[]
    if role not in {'api','migrate','scanner','intelligence','scheduler','notifier'}:
        problems.append('unknown AEGIS production service role')
    if os.getenv('FIREBASE_AUTH_EMULATOR_HOST') or os.getenv('AEGIS_FIREBASE_EMULATOR')=='true':problems.append('Firebase emulator forbidden in production')
    if connection_url().get_backend_name()!='postgresql':problems.append('PostgreSQL required')
    origin=urlsplit(os.getenv('WEB_ORIGIN',''))
    if (origin.scheme!='https' or not origin.hostname or origin.hostname in ('localhost','127.0.0.1')
        or origin.username or origin.password or origin.path not in ('','/')
        or origin.query or origin.fragment or origin.port not in (None, 443)):
        problems.append('public HTTPS WEB_ORIGIN required')
    if os.getenv('COOKIE_SECURE')!='true':problems.append('secure session cookies required')
    if os.getenv('LOCAL_FIXTURE_MODE')!='false' or os.getenv('TESTING','false').lower() not in ('false','0',''):
        problems.append('test/fixture mode forbidden')
    if (os.getenv('PAYMENTS_ENABLED','false')!='false'
        or os.getenv('PRICING_ENABLED','false')!='false'
        or os.getenv('BILLING_MODE','disabled')!='disabled'
        or os.getenv('PADDLE_ENABLED','false')!='false'
        or os.getenv('INSTAPAY_ENABLED','false')!='false'):
        problems.append('payments must remain disabled')
    try:
        redis = urlsplit(os.getenv('REDIS_URL', ''))
        if redis.scheme not in ('redis', 'rediss') or not redis.hostname or redis.query or redis.fragment:
            problems.append('Redis URL must be a redis:// or rediss:// connection origin')
        elif redis.port is not None and not 1 <= redis.port <= 65535:
            problems.append('Redis port is invalid')
    except ValueError:
        problems.append('Redis URL is invalid')
    if role in ('api','migrate'):
        if (os.getenv('FIREBASE_AUTH_ENABLED')!='true' or not all(os.getenv(k) for k in
            ('FIREBASE_PROJECT_ID','FIREBASE_WEB_API_KEY','FIREBASE_WEB_APP_ID'))):
            problems.append('Firebase authentication and public app configuration required')
        try:
            from cryptography.fernet import Fernet
            Fernet(os.environ.get('MFA_ENCRYPTION_KEY','').encode())
        except (ValueError, KeyError):
            problems.append('valid MFA encryption key required')
    if role in ('api','migrate','notifier'):
        if (os.getenv('SMTP_TLS') not in ('starttls','implicit')
            or not os.getenv('SMTP_HOST') or os.getenv('SMTP_HOST')=='disabled'
            or not os.getenv('MAIL_FROM')):
            problems.append('encrypted transactional SMTP configuration required')
    if (os.getenv('AI_ASSISTANT_ENABLED','false')!='false'
        or os.getenv('AI_PROVIDER_ENABLED','false')!='false'):
        problems.append('AI services must remain disabled for this release')
    if problems:raise RuntimeError('Deployment configuration rejected: '+ '; '.join(problems))
