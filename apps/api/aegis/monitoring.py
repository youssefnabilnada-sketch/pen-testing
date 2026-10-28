"""Durable scheduler decisions and queue outbox. Beat only triggers bounded ticks."""
import time
from sqlalchemy import select
from .db import Session
from .models import Asset, Authorization, Job, Setting, AssessmentSchedule, QueueOutbox, IntelligenceSource, Retest, Challenge
from .intelligence.service import notify, ensure_sources, synchronize
from .worker import celery

CADENCE={'daily':86400,'weekly':7*86400,'monthly':30*86400}


def enqueue(db,asset,authorization_id):
    db.scalar(select(Asset).where(Asset.id==asset.id).with_for_update())
    auth=db.get(Authorization,authorization_id)
    paused=db.get(Setting,'scans_paused');now=time.time()
    if paused and paused.value:raise ValueError('Assessments are paused.')
    if not auth or auth.asset_id!=asset.id or auth.revoked or auth.expires<=now or asset.verified_until<=now:
        raise ValueError('Current verified ownership and exact-scope authorization required.')
    from .scope import require_supported_scope
    require_supported_scope(auth.scope,asset.origin)
    from .windows import require_window
    require_window(auth,now)
    if db.scalar(select(Job).where(Job.asset_id==asset.id,Job.status.not_in(['completed','failed','cancelled','partially_completed']))):raise ValueError('An assessment is already active.')
    recent=db.scalar(select(Job).where(Job.asset_id==asset.id,Job.created>now-60).order_by(Job.created.desc()))
    if recent:raise ValueError('Target cooldown: wait 60 seconds.')
    job=Job(org_id=asset.org_id,asset_id=asset.id,authorization_id=auth.id);db.add(job);db.flush()
    db.add(QueueOutbox(job_id=job.id));db.flush()
    return job


@celery.task(name='aegis.dispatch_outbox')
def dispatch_outbox():
    from .worker import assess
    with Session() as db:
        records=db.scalars(select(QueueOutbox).where(QueueOutbox.dispatched.is_(False),QueueOutbox.next_attempt<=time.time()).with_for_update(skip_locked=True).limit(50)).all()
        for row in records:
            row.attempts+=1
            if db.get(Job,row.job_id).status!='queued':row.dispatched=True;continue
            try:
                assess.apply_async(args=[row.job_id],queue='celery',task_id='assessment-'+row.job_id)
                row.dispatched=True;row.error=None
            except Exception:
                row.error='Broker delivery failed; pending durable retry.';row.next_attempt=time.time()+min(300,2**min(row.attempts,8))
        db.commit()
        return len(records)


@celery.task(name='aegis.monitor_tick')
def monitor_tick():
    now=time.time();created=[]
    with Session() as db:
        schedules=db.scalars(select(AssessmentSchedule).where(AssessmentSchedule.enabled.is_(True),AssessmentSchedule.next_due<=now).with_for_update(skip_locked=True).limit(100)).all()
        for s in schedules:
            try:
                asset=db.get(Asset,s.asset_id)
                auth=db.get(Authorization,s.authorization_id)
                if auth and not auth.revoked and auth.expires>now:
                    from .windows import next_allowed
                    eligible=next_allowed(auth.scope,now)
                    if eligible>now:
                        s.next_due=min(eligible,auth.expires);s.status='waiting_window';continue
                if s.reverify and auth and not auth.revoked and auth.expires>now and asset.verified_until<=now:
                    challenge=db.scalar(select(Challenge).where(Challenge.asset_id==asset.id,Challenge.consumed.is_(True)).order_by(Challenge.created.desc()))
                    from .verification import verify
                    try:
                        proof=bool(challenge and verify(asset.origin,challenge))
                    except Exception:
                        proof=False
                    if not proof:raise ValueError('Scheduled ownership re-verification failed.')
                    asset.verified_until=min(now+86400,auth.expires)
                job=enqueue(db,asset,s.authorization_id)
                s.last_job_id=job.id;s.last_run=now;s.next_due=now+CADENCE[s.cadence];s.status='queued';created.append(job.id)
            except ValueError as exc:
                s.status='blocked';s.next_due=now+3600
                notify(db,s.org_id,'schedule_blocked','schedule-blocked:'+s.id+':'+s.authorization_id,'Scheduled assessment could not run',str(exc)+' Authorization is never renewed automatically.',s.asset_id)
        db.commit()
    dispatch_outbox.delay()
    return created


@celery.task(name='aegis.sync_intelligence',time_limit=300,soft_time_limit=270)
def sync_intelligence(source):return synchronize(source)


@celery.task(name='aegis.intelligence_tick')
def intelligence_tick():
    now=time.time();due=[]
    with Session() as db:
        ensure_sources(db);db.commit()
        for s in db.scalars(select(IntelligenceSource).where(IntelligenceSource.enabled.is_(True),IntelligenceSource.next_due<=now,IntelligenceSource.lease_until<now).with_for_update(skip_locked=True)):
            # Reserve dispatch briefly; sync owns the execution lease and backoff.
            s.next_due=now+300;due.append(s.key)
        db.commit()
    for key in due:
        try:sync_intelligence.apply_async(args=[key],queue='intelligence')
        except Exception:
            with Session() as db:
                s=db.get(IntelligenceSource,key);s.error='Queue dispatch failed; retry due in five minutes.';db.commit()
    return due
