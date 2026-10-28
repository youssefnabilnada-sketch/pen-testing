import os
import time
import logging
from copy import deepcopy
from celery import Celery
from sqlalchemy import select, update
from .db import Session
from .models import Job, Asset, Authorization, Finding, FindingHistory, Report, Organization, Setting, Audit, AssessmentSchedule
from .safety import fetch
from .checks import analyze
from .runtime import validate_runtime

validate_runtime()

logger=logging.getLogger(__name__)
celery=Celery('aegis',broker=os.getenv('REDIS_URL','redis://localhost:6379/0'))
celery.conf.imports=('aegis.monitoring','aegis.health_monitoring','aegis.email_alerts')
celery.conf.beat_schedule={
 'monitor-assets':{'task':'aegis.monitor_tick','schedule':60.0},
 'email-alerts':{'task':'aegis.email_tick','schedule':30.0},
 'website-health':{'task':'aegis.health_tick','schedule':60.0},
 'retry-outbox':{'task':'aegis.dispatch_outbox','schedule':30.0},
 'sync-advisory-sources':{'task':'aegis.intelligence_tick','schedule':300.0},
}
celery.conf.update(task_serializer='json',accept_content=['json'],result_serializer='json',task_acks_late=True,worker_prefetch_multiplier=1,task_time_limit=300,task_soft_time_limit=280,broker_connection_retry_on_startup=True,task_reject_on_worker_lost=False)
TERMINAL=('completed','partially_completed','failed','cancelled')

class Cancelled(Exception):pass
class AlreadyTerminal(Exception):pass

def checkpoint(db,job,status,progress):
    db.refresh(job)
    if job.status in TERMINAL:raise AlreadyTerminal()
    a=db.get(Asset,job.asset_id);db.refresh(a)
    auth=db.get(Authorization,job.authorization_id);db.refresh(auth)
    paused=db.get(Setting,'scans_paused')
    if job.cancel or (paused and paused.value):raise Cancelled()
    if not auth or auth.revoked or auth.expires<=time.time() or a.verified_until<=time.time():
        raise ValueError('Authorization expired, revoked or scope mismatched.')
    from .scope import require_supported_scope
    require_supported_scope(auth.scope,a.origin)
    from .windows import require_window
    require_window(auth,time.time())
    job.status=status;job.progress=progress;db.commit()
    logger.info('assessment_checkpoint',extra={'job_id':job.id,'state':status,'progress':progress})

@celery.task(name='aegis.assess')
def assess(job_id):
    with Session() as db:
        # Compare-and-swap claim prevents a redelivered task from repeating network traffic.
        claimed=db.execute(update(Job).where(Job.id==job_id,Job.status=='queued').values(status='preparing',progress=5))
        db.commit()
        if not claimed.rowcount:return
        job=db.get(Job,job_id)
        try:
            checkpoint(db,job,'preparing',10)
            a=db.get(Asset,job.asset_id)
            if os.getenv('TESTING')!='1':
                import redis
                import hashlib
                r=redis.Redis.from_url(os.getenv('REDIS_URL','redis://localhost:6379/0'))
                key='target-cooldown:'+hashlib.sha256(a.origin.encode()).hexdigest()
                if not r.set(key,job.id,nx=True,ex=60):
                    raise ValueError('Target cooldown active. Wait 60 seconds before submitting another assessment.')
            checkpoint(db,job,'running',25)
            from .safety import authorization_guard
            from .regression import profile, finish_retest, advisory_evaluation
            from .intelligence.service import notify
            from .multipath import combine
            scope=deepcopy(db.get(Authorization,job.authorization_id).scope)
            results=[]
            for index,path in enumerate(scope['paths']):
                if index:time.sleep(1)
                def guard():
                    checkpoint(db,job,'running',25+int(index*30/len(scope['paths'])))
                    if db.get(Authorization,job.authorization_id).scope!=scope:raise ValueError('Scope changed during execution.')
                with authorization_guard(guard):
                    guard()
                    response=fetch(a.origin) if scope['paths']==['/'] else fetch(a.origin,path,assessment_scope=scope)
                if not 200<=response.status<300:raise ValueError('Non-success response; no clean result implied.')
                if scope['type']=='api-response-configuration':
                    from .api_assessment import profile as api_profile
                    found,manifest=api_profile(a.origin,response)
                else:found,manifest=profile(db,a.origin,response)
                results.append((path,found,manifest))
            checkpoint(db,job,'processing_results',60)
            if db.get(Authorization,job.authorization_id).scope!=scope:raise ValueError('Scope changed during execution.')
            observations,manifest=(results[0][1],results[0][2]) if scope['paths']==['/'] else combine(results)
            # A completed root-only assessment also needs an explicit observed-path
            # manifest. Staging verification must never infer coverage from a
            # missing field or treat a partial response as a verified fix.
            manifest={**manifest,'paths':[path for path,_,_ in results]}
            # Stage all findings plus immutable report snapshot in one transaction.
            job.observations=observations
            seen={o['rule'] for o in observations}
            for o in observations:
                f=db.scalar(select(Finding).where(Finding.asset_id==a.id,Finding.rule==o['rule']))
                previous_status=f.status if f else None
                if not f:
                    f=Finding(org_id=a.org_id,asset_id=a.id,job_id=job.id,**{k:o[k] for k in ('rule','title','severity','confidence','evidence','remediation')});db.add(f);db.flush()
                else:
                    f.job_id=job.id;f.last_observed=time.time();f.evidence=o['evidence']
                    if f.status=='resolved':f.status='reopened'
                db.add(FindingHistory(finding_id=f.id,job_id=job.id,status=f.status))
                if previous_status is None or previous_status=='resolved':
                    notify(db,a.org_id,'finding_change','finding:'+job.id+':'+f.rule,'New or recurring security observation',f.title+'; review context and approved remediation guidance.',f.id)
            for f in db.scalars(select(Finding).where(Finding.asset_id==a.id)):
                if f.rule not in seen and f.rule in manifest['executed'] and f.status not in ('accepted_risk','false_positive','resolved'):
                    f.status='resolved';db.add(FindingHistory(finding_id=f.id,job_id=job.id,status='resolved'))
            comparison=finish_retest(db,job,observations,manifest)
            job.status='generating_report';job.progress=85
            snapshot={'organization':db.get(Organization,a.org_id).name,'origin':a.origin,'job_id':job.id,'date':time.time(),'status':'completed','findings':observations,'scope':db.get(Authorization,job.authorization_id).scope,'profile':manifest,'comparison':comparison,'advisory_evaluation':advisory_evaluation(db,a.id)}
            from .reporting import render_pdf
            render_pdf(snapshot)  # Verify report generation before marking complete; download uses immutable snapshot.
            report=Report(job_id=job.id,org_id=a.org_id,snapshot=snapshot)
            db.add(report);db.flush()
            from .evidence_vault import seal
            seal(db,report)
            # Cancellation/revocation arriving during result processing rolls back the result transaction.
            with Session() as check:
                latest=check.get(Job,job.id);auth=check.get(Authorization,job.authorization_id);asset=check.get(Asset,job.asset_id);paused=check.get(Setting,'scans_paused')
                if latest.status in TERMINAL:raise AlreadyTerminal()
                if latest.cancel or (paused and paused.value):raise Cancelled()
                if auth.scope!=scope:raise ValueError('Scope changed during assessment.')
                if auth.revoked or auth.expires<=time.time() or asset.verified_until<=time.time():raise ValueError('Authorization expired during assessment.')
            job.status='completed';job.progress=100;job.finished=time.time()
            for schedule in db.scalars(select(AssessmentSchedule).where(AssessmentSchedule.last_job_id==job.id)):schedule.status=job.status
            db.add(Audit(org_id=a.org_id,action='assessment.completed',target=job.id));db.commit()
        except Exception as exc:
            db.rollback();job=db.get(Job,job_id)
            if job.status in TERMINAL:return
            job.status='cancelled' if isinstance(exc,Cancelled) else 'failed'
            job.error=None if isinstance(exc,Cancelled) else ('Assessment failed: '+type(exc).__name__+'. No clean result is implied.')
            from .models import Retest
            from .intelligence.service import notify
            r=db.scalar(select(Retest).where(Retest.job_id==job.id))
            if r:
                r.status='unverified';r.comparison={**r.comparison,'failure':'Assessment did not complete; no fix verified.'}
            notify(db,job.org_id,'assessment_failed','job-failure:'+job.id,'Assessment '+job.status,'No clean result or verified fix is implied.',job.id)
            for schedule in db.scalars(select(AssessmentSchedule).where(AssessmentSchedule.last_job_id==job.id)):schedule.status=job.status
            job.finished=time.time();db.add(Audit(org_id=job.org_id,action='assessment.'+job.status,target=job.id));db.commit()
            logger.warning('assessment_stopped',extra={'job_id':job_id,'error_type':type(exc).__name__})
