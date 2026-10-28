"""Opt-in security alerts. SMTP acceptance is not inbox delivery confirmation."""
import os,time
from email.message import EmailMessage
from fastapi import APIRouter,Depends
from sqlalchemy import select,update
from .auth import current,member,audit,smtp_connection
from .db import database,Session
from .models import AlertSubscription,EmailDelivery,Notification,Membership,User
from .notifications import Preferences
from .worker import celery
router=APIRouter(tags=['Security Guardian email alerts'])

@router.get('/organizations/{org}/email-preferences')
def get_preferences(org:str,u=Depends(current),db=Depends(database)):
    member(db,u,org)
    row=db.scalar(select(AlertSubscription).where(AlertSubscription.org_id==org,AlertSubscription.user_id==u.id))
    return {'enabled_kinds':row.kinds if row else [],'channel':'email','delivery_semantics':'SMTP accepted does not confirm inbox delivery.'}

@router.put('/organizations/{org}/email-preferences')
def put_preferences(org:str,data:Preferences,u=Depends(current),db=Depends(database)):
    member(db,u,org);db.scalar(select(User).where(User.id==u.id).with_for_update())
    row=db.scalar(select(AlertSubscription).where(AlertSubscription.org_id==org,AlertSubscription.user_id==u.id))
    if not row:row=AlertSubscription(org_id=org,user_id=u.id,kinds=[]);db.add(row)
    row.kinds=sorted(set(data.enabled_kinds));audit(db,u,'email.preferences_changed',u.id,org);db.commit()
    return {'enabled_kinds':row.kinds}

@router.get('/organizations/{org}/email-history')
def history(org:str,u=Depends(current),db=Depends(database)):
    member(db,u,org)
    rows=db.execute(select(EmailDelivery,Notification).join(Notification,Notification.id==EmailDelivery.notification_id).where(Notification.org_id==org,EmailDelivery.user_id==u.id).order_by(EmailDelivery.created.desc()).limit(100))
    return [{'id':d.id,'created':d.created,'title':n.title,'status':d.status,'attempts':d.attempts,'error':d.error} for d,n in rows]

def queue_alert(db,notification):
    subscriptions=db.scalars(select(AlertSubscription).where(AlertSubscription.org_id==notification.org_id))
    for s in subscriptions:
        if notification.kind in s.kinds:
            db.add(EmailDelivery(notification_id=notification.id,user_id=s.user_id))

@celery.task(name='aegis.send_alert',time_limit=30,soft_time_limit=25)
def send_alert(delivery_id):
    with Session() as db:
        now=time.time()
        claimed=db.execute(update(EmailDelivery).where(EmailDelivery.id==delivery_id,EmailDelivery.status.in_(['pending','sending']),EmailDelivery.next_due<=now,EmailDelivery.attempts<5).values(status='sending',next_due=now+120,attempts=EmailDelivery.attempts+1))
        db.commit()
        if not claimed.rowcount:return
        d=db.get(EmailDelivery,delivery_id);n=db.get(Notification,d.notification_id);u=db.get(User,d.user_id)
        s=db.scalar(select(AlertSubscription).where(AlertSubscription.org_id==n.org_id,AlertSubscription.user_id==u.id))
        membership=db.scalar(select(Membership).where(Membership.org_id==n.org_id,Membership.user_id==u.id))
        if not membership or not u.active or not u.verified or not s or n.kind not in s.kinds:
            d.status='cancelled';d.error='Recipient consent or workspace access no longer valid.';db.commit();return
        msg=EmailMessage();msg['From']=os.getenv('MAIL_FROM','security@aegis.local');msg['To']=u.email
        msg['Subject']='AEGIS security notification';msg['Message-ID']=f'<aegis-alert-{d.id}@notifications.aegis>'
        msg.set_content('A new notification is available in your AEGIS workspace.\n\n'+n.title[:200]+'\n\nSign in to review the evidence: '+os.getenv('WEB_ORIGIN','http://localhost:3000').rstrip('/')+'/console\n\nManage email preferences in your workspace. No website changes were authorized by this message.')
        try:
            with smtp_connection() as smtp:
                refused=smtp.send_message(msg)
                if refused:raise OSError('Recipient refused')
            d.status='smtp_accepted';d.error=''
        except Exception:
            d.status='failed' if d.attempts>=5 else 'pending';d.error='SMTP delivery attempt failed; no inbox delivery is claimed.'
            d.next_due=time.time()+min(3600,30*2**d.attempts)
        db.commit()

@celery.task(name='aegis.email_tick')
def tick():
    with Session() as db:
        # A worker may die after claiming its final attempt. Do not leave it
        # permanently sending, and do not assert that SMTP did not accept it.
        db.execute(update(EmailDelivery).where(
            EmailDelivery.status.in_(['pending','sending']),
            EmailDelivery.next_due<=time.time(),EmailDelivery.attempts>=5
        ).values(status='failed',error='Retry budget exhausted; last delivery outcome may be unknown.'))
        db.commit()
        ids=list(db.scalars(select(EmailDelivery.id).where(EmailDelivery.status.in_(['pending','sending']),EmailDelivery.next_due<=time.time(),EmailDelivery.attempts<5).order_by(EmailDelivery.created).limit(20)))
    dispatched=0
    for delivery_id in ids:
        try:
            send_alert.delay(delivery_id);dispatched+=1
        except Exception:
            # Leave the durable row eligible; the next tick retries dispatch.
            # A single broker failure must not discard the rest of this batch.
            continue
    return dispatched
