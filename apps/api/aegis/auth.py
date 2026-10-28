import hashlib
import os
import secrets
import time
import smtplib
import ssl
from email.message import EmailMessage
from argon2 import PasswordHasher
from fastapi import HTTPException, Request, Depends
from sqlalchemy import select
from .db import database
from .models import User, LoginSession, Membership, Audit

hasher = PasswordHasher()

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def current(request: Request, db=Depends(database)):
    session = db.scalar(select(LoginSession).where(LoginSession.token_hash == digest(request.cookies.get('aegis_session', ''))))
    if not session or session.expires < time.time():
        raise HTTPException(401, 'Sign in to continue.')
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, 'Account unavailable.')
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if not secrets.compare_digest(request.headers.get('x-csrf-token', ''), session.csrf):
            raise HTTPException(403, 'CSRF validation failed.')
    return user

def member(db, user, org_id, write=False, roles=None):
    # Platform staff access is explicit and audited by each mutation; ordinary routes do not bypass tenancy.
    m = db.scalar(select(Membership).where(Membership.org_id == org_id, Membership.user_id == user.id))
    if not m or (write and m.role == 'viewer') or (roles and m.role not in roles):
        raise HTTPException(403, 'Workspace permission required.')
    return m

def admin(user):
    if not user.superadmin:
        raise HTTPException(403, 'Platform administrator required.')

def audit(db, user, action, target, org_id=None):
    db.add(Audit(user_id=user.id if user else None, action=action, target=target, org_id=org_id))

def send_token(email, token, purpose):
    message = EmailMessage()
    message['From'] = os.getenv('MAIL_FROM', 'security@aegis.local')
    message['To'] = email
    message['Subject'] = f'AEGIS: {purpose}'
    if purpose not in ('verify','reset'):
        raise ValueError('Unsupported account email purpose.')
    # Fragment stays in the browser; it is not transmitted in HTTP requests/referrers.
    from urllib.parse import quote
    link=os.getenv('WEB_ORIGIN','http://localhost:3000').rstrip('/')+'/console#'+purpose+'='+quote(token,safe='')
    message.set_content(f'Open this link to review and complete your {purpose} request (valid for 30 minutes):\n{link}\n\nAlternative one-time token:\n{token}\nNever share this link or token. Opening the link alone does not change your account.')
    with smtp_connection() as smtp:
        smtp.send_message(message)

def smtp_connection():
    host=os.getenv('SMTP_HOST','localhost')
    port=int(os.getenv('SMTP_PORT','1025'))
    mode=os.getenv('SMTP_TLS','none')
    if os.getenv('AEGIS_ENV')=='production' and mode not in ('starttls','implicit'):
        raise OSError('Encrypted SMTP is required for public deployment.')
    smtp=None
    try:
        if mode=='implicit':
            smtp=smtplib.SMTP_SSL(host,port,timeout=5,context=ssl.create_default_context())
        else:
            smtp=smtplib.SMTP(host,port,timeout=5)
            if mode=='starttls':
                smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo()
            elif mode!='none':raise OSError('Unsupported SMTP TLS mode.')
        if os.getenv('SMTP_USERNAME'):
            smtp.login(os.environ['SMTP_USERNAME'],os.getenv('SMTP_PASSWORD',''))
        return smtp
    except Exception:
        if smtp:
            try:smtp.close()
            except Exception:pass
        raise OSError('Email transport could not be established.') from None
