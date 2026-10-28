from ..notifications import visible as visible_notifications,mark_read
import json
import re
import time
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from ..db import database
from ..auth import current, member, admin, audit
from ..models import Asset, Advisory, KnowledgeRevision, InventoryItem, AdvisoryImpact, IntelligenceSource, SyncRun, Notification, AssessmentSchedule, Authorization, Retest, Job, Finding, Report, Remediation, DetectionRule
from .service import ensure_sources, match_inventory, grounded_guidance, notify, normalize_name
from .safe_history import inventory_view, impact_view, schedule_view, baseline_paths
from .feeds import SOURCES, REFERENCE_PAGES
from ..monitoring import enqueue, dispatch_outbox, sync_intelligence, CADENCE
router=APIRouter()


def asset_for(db,u,asset_id,roles=None):
    a=db.get(Asset,asset_id)
    if not a:raise HTTPException(404,'Asset not found.')
    member(db,u,a.org_id,roles=roles)
    return a


def fix_for(db,u,rid,roles=None):
    r=db.get(Remediation,rid)
    if not r:raise HTTPException(404,'Remediation not found.')
    member(db,u,r.org_id,roles=roles)
    return r


def source_dict(s):
    return {'key':s.key,'enabled':s.enabled,'interval_hours':s.interval_hours,'last_attempt':s.last_attempt,'last_success':s.last_success,'next_due':s.next_due,'failures':s.failures,'error':s.error,'documentation':REFERENCE_PAGES[s.key],'coverage':'known GHSA identifiers only' if s.key=='osv' else 'full catalog' if s.key=='cisa' else 'incremental; starts at last 24 hours'}


def advisory_dict(db,a):
    revisions=db.scalars(select(KnowledgeRevision).where(KnowledgeRevision.advisory_id==a.id,KnowledgeRevision.current.is_(True))).all()
    return {'id':a.id,'identifier':a.identifier,'title':a.title,'severity':a.severity,'actively_exploited':a.exploited,'updated':a.updated,
        'classification':'global advisory; not a confirmed customer finding','revisions':[{'id':r.id,'source':r.source,'approved':r.approved_at is not None,'content':r.content} for r in revisions]}


@router.get('/intelligence/advisories')
def advisories(q:str='',exploited:bool=False,offset:int=0,u=Depends(current),db=Depends(database)):
    stmt=select(Advisory)
    if q:stmt=stmt.where(Advisory.title.ilike('%'+q[:100]+'%')|Advisory.identifier.ilike('%'+q[:100]+'%'))
    if exploited:stmt=stmt.where(Advisory.exploited.is_(True))
    return [advisory_dict(db,a) for a in db.scalars(stmt.order_by(Advisory.exploited.desc(),Advisory.updated.desc()).offset(max(0,offset)).limit(50))]


@router.get('/intelligence/sources')
def sources(u=Depends(current),db=Depends(database)):
    ensure_sources(db);db.commit()
    return [source_dict(s) for s in db.scalars(select(IntelligenceSource))]


@router.get('/intelligence/knowledge')
def knowledge(q:str='',u=Depends(current),db=Depends(database)):
    return grounded_guidance(db,q[:300])


@router.post('/admin/intelligence/revisions/{revision_id}/approve')
def approve_knowledge(revision_id:str,u=Depends(current),db=Depends(database)):
    admin(u);r=db.get(KnowledgeRevision,revision_id)
    if not r or not r.current or r.content['withdrawn']:raise HTTPException(409,'Only a current non-withdrawn revision can be approved.')
    r.approved_by=u.id;r.approved_at=time.time();audit(db,u,'knowledge.approved',r.id);db.commit()
    return {'revision_id':r.id,'approved':True,'model_weights_retrained':False}


class SourceSettings(BaseModel):
    enabled:bool
    interval_hours:int=Field(ge=6,le=12)

@router.patch('/admin/intelligence/sources/{key}')
def source_settings(key:str,data:SourceSettings,u=Depends(current),db=Depends(database)):
    admin(u);ensure_sources(db);s=db.get(IntelligenceSource,key)
    if not s:raise HTTPException(404,'Unknown source; arbitrary feed URLs are not accepted.')
    s.enabled=data.enabled;s.interval_hours=data.interval_hours;s.next_due=time.time()
    audit(db,u,'intelligence.source_configured',key);db.commit();return source_dict(s)

@router.post('/admin/intelligence/sources/{key}/sync')
def source_sync(key:str,u=Depends(current),db=Depends(database)):
    admin(u)
    if key not in SOURCES:raise HTTPException(404,'Unknown source.')
    ensure_sources(db);db.commit()
    try:sync_intelligence.apply_async(args=[key],queue='intelligence')
    except Exception:raise HTTPException(503,'Intelligence queue unavailable; no successful sync claimed.')
    return {'status':'queued'}

@router.get('/admin/intelligence/runs')
def runs(u=Depends(current),db=Depends(database)):
    admin(u)
    return [{'id':r.id,'source':r.source,'status':r.status,'records':r.records,'created':r.created,'finished':r.finished,'error':r.error} for r in db.scalars(select(SyncRun).order_by(SyncRun.created.desc()).limit(100))]


class InventoryInput(BaseModel):
    ecosystem:str=Field(pattern=r'^(PyPI|npm|vendor|cpe)$')
    package:str=Field(min_length=1,max_length=200)
    version:str=Field(max_length=100)
    evidence:str=Field(min_length=5,max_length=500)


def put_inventory(db,a,data):
    package=normalize_name(data.ecosystem,data.package.strip())
    if any(ord(c)<32 for c in package+data.version):raise HTTPException(422,'Invalid package or version.')
    i=db.scalar(select(InventoryItem).where(InventoryItem.asset_id==a.id,InventoryItem.ecosystem==data.ecosystem,InventoryItem.package==package))
    if not i:
        i=InventoryItem(org_id=a.org_id,asset_id=a.id,ecosystem=data.ecosystem,package=package,version=data.version,evidence=data.evidence);db.add(i)
    else:i.version=data.version;i.evidence=data.evidence;i.updated=time.time()
    db.flush();return i

@router.post('/assets/{asset_id}/inventory')
def inventory_add(asset_id:str,data:InventoryInput,u=Depends(current),db=Depends(database)):
    a=asset_for(db,u,asset_id,['owner','admin','analyst']);i=put_inventory(db,a,data)
    match_inventory(db,a.org_id);audit(db,u,'inventory.updated',i.id,a.org_id);db.commit()
    return {'id':i.id,'source':'customer-declared; no intrusive fingerprinting'}

class ManifestInput(BaseModel):
    format:str=Field(pattern=r'^(requirements|package-lock)$')
    content:str=Field(min_length=1,max_length=1000000)

@router.post('/assets/{asset_id}/inventory/import')
def import_manifest(asset_id:str,data:ManifestInput,u=Depends(current),db=Depends(database)):
    a=asset_for(db,u,asset_id,['owner','admin','analyst']);items=[]
    try:
        if data.format=='requirements':
            for line in data.content.splitlines():
                line=line.strip()
                if not line or line.startswith('#'):continue
                m=re.fullmatch(r'([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)',line)
                if not m:raise ValueError('Only exact name==version entries are accepted; no URLs, directives or environment markers.')
                items.append(InventoryInput(ecosystem='PyPI',package=m[1],version=m[2],evidence='Customer imported exact requirements manifest'))
        else:
            payload=json.loads(data.content)
            if payload.get('lockfileVersion') not in (2,3):raise ValueError('Only npm lockfile versions 2 and 3 supported.')
            for path,value in payload['packages'].items():
                if not path or 'node_modules/' not in path:continue
                package=path.rsplit('node_modules/',1)[1]
                items.append(InventoryInput(ecosystem='npm',package=package,version=value['version'],evidence='Customer imported npm lockfile'))
        if not items or len(items)>2000:raise ValueError('Manifest requires 1–2000 exact package entries.')
        # Duplicate package versions need per-component identity, not silent replacement.
        versions={}
        for i in items:
            key=(i.ecosystem,normalize_name(i.ecosystem,i.package))
            if key in versions and versions[key]!=i.version:raise ValueError('Multiple versions of one package require separate inventory identities; import rejected without partial changes.')
            versions[key]=i.version
        for i in items:put_inventory(db,a,i)
        match_inventory(db,a.org_id);audit(db,u,'inventory.manifest_imported',a.id,a.org_id);db.commit()
        return {'imported':len(versions),'external_inventory_disclosure':False}
    except (ValueError,KeyError,TypeError) as exc:raise HTTPException(422,str(exc))


@router.get('/organizations/{org_id}/intelligence')
def organization_intelligence(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    inventory=db.scalars(select(InventoryItem).where(InventoryItem.org_id==org_id)).all()
    return {'inventory': [inventory_view(db, i, org_id) for i in inventory],
        'impacts': [impact_view(db, i, org_id) for i in db.scalars(
            select(AdvisoryImpact).where(AdvisoryImpact.org_id == org_id))],
        'notifications': visible_notifications(db, u, org_id),
        'schedules': [schedule_view(db, s, org_id) for s in db.scalars(
            select(AssessmentSchedule).where(AssessmentSchedule.org_id == org_id))],
        'retests': [{'id': r.id, 'remediation_id': r.remediation_id,
                     'job_id': r.job_id if (job := db.get(Job, r.job_id)) and job.org_id == org_id else None,
                     'status': r.status, 'comparison': r.comparison if isinstance(r.comparison, dict) else {},
                     'created': r.created}
                    for r in db.scalars(select(Retest).where(Retest.org_id == org_id)
                                         .order_by(Retest.created.desc()).limit(100))]}


@router.get('/organizations/{org_id}/intelligence/report.pdf')
def intelligence_pdf(org_id: str, u=Depends(current), db=Depends(database)):
    """A tenant-scoped advisory-match snapshot, not vulnerability certification."""
    member(db, u, org_id)
    inventory = [inventory_view(db, i, org_id) for i in db.scalars(
        select(InventoryItem).where(InventoryItem.org_id == org_id)
        .order_by(InventoryItem.updated.desc()).limit(100))]
    impacts = [impact_view(db, i, org_id) for i in db.scalars(
        select(AdvisoryImpact).where(AdvisoryImpact.org_id == org_id)
        .order_by(AdvisoryImpact.updated.desc()).limit(100))]
    from ..reporting import render_intelligence_pdf
    result = render_intelligence_pdf(org_id, inventory, impacts)
    return Response(result.getvalue(), media_type='application/pdf',
                    headers={'Content-Disposition':'attachment; filename="aegis-intelligence-evidence.pdf"',
                             'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff'})


@router.post('/notifications/{notification_id}/read')
def notification_read(notification_id:str,u=Depends(current),db=Depends(database)):
    n=db.get(Notification,notification_id)
    if not n:raise HTTPException(404,'Notification not found.')
    return mark_read(db,u,n)

class ScheduleInput(BaseModel):
    paths:list[str]=Field(default_factory=lambda:['/'],min_length=1,max_length=20)
    cadence:str=Field(pattern=r'^(daily|weekly|monthly)$')
    consent_days:int=Field(default=30,ge=1,le=90)
    accepted:bool
    on_advisory:bool=False
    reverify:bool=True
    start_hour_utc:int=Field(default=0,ge=0,le=23)
    end_hour_utc:int=Field(default=24,ge=1,le=24)

@router.post('/assets/{asset_id}/schedule')
def create_schedule(asset_id:str,data:ScheduleInput,u=Depends(current),db=Depends(database)):
    a=asset_for(db,u,asset_id,['owner','admin','analyst'])
    if not data.accepted or a.verified_until<=time.time():raise HTTPException(403,'Verified ownership and explicit recurring-assessment consent required.')
    from ..multipath import validate_paths
    try:validate_paths(data.paths)
    except ValueError as exc:raise HTTPException(422,str(exc))
    if data.start_hour_utc>=data.end_hour_utc:raise HTTPException(422,'Daily UTC window start must precede its end.')
    auth=Authorization(asset_id=a.id,user_id=u.id,expires=time.time()+data.consent_days*86400,scope={'origin':a.origin,'paths':['/'],'request_limit':1,'timeout_seconds':5,'type':'root-response-configuration','window_start':time.time(),'daily_window_utc':[data.start_hour_utc,data.end_hour_utc],'recurring':True,'cadence':data.cadence,'reverify':data.reverify,'on_advisory':data.on_advisory})
    if data.paths!=['/']:auth.scope={**auth.scope,'paths':data.paths,'request_limit':len(data.paths),'type':'explicit-path-response','method':'GET'}
    db.add(auth);db.flush()
    s=db.scalar(select(AssessmentSchedule).where(AssessmentSchedule.asset_id==a.id))
    if not s:s=AssessmentSchedule(org_id=a.org_id,asset_id=a.id,authorization_id=auth.id,cadence=data.cadence,next_due=time.time());db.add(s)
    else:
        old=db.get(Authorization,s.authorization_id)
        if old:
            old.revoked=True
        s.authorization_id=auth.id;s.cadence=data.cadence;s.next_due=time.time();s.status='scheduled';s.enabled=True
    s.on_advisory=data.on_advisory;s.reverify=data.reverify
    audit(db,u,'monitoring.consent_recorded',a.id,a.org_id);db.commit()
    return {'id':s.id,'authorization_expires':auth.expires,'next_due':s.next_due,'monthly_semantics':'every 30 days','scope':auth.scope}

@router.delete('/schedules/{schedule_id}')
def disable_schedule(schedule_id:str,u=Depends(current),db=Depends(database)):
    s=db.get(AssessmentSchedule,schedule_id)
    if not s:raise HTTPException(404,'Schedule not found.')
    member(db,u,s.org_id,roles=['owner','admin','analyst']);s.enabled=False
    previous_auth=db.get(Authorization,s.authorization_id)
    if previous_auth:
        previous_auth.revoked=True
    for j in db.scalars(select(Job).where(Job.authorization_id==s.authorization_id,Job.status.not_in(['completed','failed','cancelled']))):j.cancel=True
    audit(db,u,'monitoring.disabled',s.id,s.org_id);db.commit();return {'enabled':False}


@router.get('/remediations/{request_id}/plan')
def remediation_plan(request_id:str,u=Depends(current),db=Depends(database)):
    r=fix_for(db,u,request_id);f=db.get(Finding,r.finding_id)
    inventory=list(db.scalars(select(InventoryItem).where(InventoryItem.asset_id==f.asset_id,InventoryItem.org_id==r.org_id)))
    plan=grounded_guidance(db,f.title+' '+' '.join(i.package for i in inventory))
    plan['original_finding']={'id':f.id,'rule':f.rule,'supported_configuration_fix':f.remediation}
    plan['source_code_access']='No repository connection exists. Engineer-managed guidance only; no patch applied.'
    return plan

class AppliedInput(BaseModel):
    evidence:str=Field(min_length=20,max_length=8000)
    rollback_plan:str=Field(min_length=20,max_length=8000)
    staging_validation:str=Field(min_length=20,max_length=8000)

@router.get('/remediations/{request_id}/retests')
def remediation_retests(request_id:str,u=Depends(current),db=Depends(database)):
    r=fix_for(db,u,request_id)
    from ..models import Report
    rows=db.scalars(select(Retest).where(Retest.remediation_id==r.id).order_by(Retest.created.desc()).limit(50)).all()
    result=[]
    for t in rows:
        # A stale/corrupted foreign-key edge must not expose a different tenant's
        # job or report, even if a Retest row points to our remediation.
        if t.org_id != r.org_id:
            continue
        job = db.get(Job, t.job_id) if t.job_id else None
        if job and job.org_id != r.org_id:
            job = None
        report = db.scalar(select(Report).where(Report.job_id == job.id, Report.org_id == r.org_id)) if job else None
        paths = baseline_paths(db, t, r.org_id, r)
        result.append({'id':t.id,'status':t.status,'created':t.created,
            'evidence':t.evidence,'rollback_plan':t.rollback_plan,'staging_validation':t.staging_validation,
            'job_id':job.id if job else None,'job_status':job.status if job else None,
            'comparison':t.comparison if isinstance(t.comparison, dict) else {},
            'report_available':bool(report),'approved_by':t.approved_by,
            'paths':paths,'baseline_paths_available':paths is not None})
    return result

@router.post('/remediations/{request_id}/applied')
def record_applied(request_id:str,data:AppliedInput,u=Depends(current),db=Depends(database)):
    r=fix_for(db,u,request_id,['owner','admin','engineer'])
    db.scalar(select(Remediation).where(Remediation.id==r.id).with_for_update())
    if r.status not in ('in_progress','ready_for_retest'):raise HTTPException(409,'Accepted scope and active engineering work required.')
    previous=db.scalar(select(Retest).where(Retest.remediation_id==r.id,Retest.status.in_(['awaiting_approval','queued'])))
    if previous:raise HTTPException(409,'A change is already awaiting approval or retest.')
    f=db.get(Finding,r.finding_id)
    baseline=db.scalar(select(Job).where(Job.asset_id==f.asset_id,Job.status=='completed').order_by(Job.created.desc()))
    if not baseline:raise HTTPException(409,'A completed assessment baseline is required.')
    all_findings=db.scalars(select(Finding).where(Finding.asset_id==f.asset_id)).all()
    t=Retest(org_id=r.org_id,remediation_id=r.id,baseline_job_id=baseline.id,evidence=data.evidence,rollback_plan=data.rollback_plan,staging_validation=data.staging_validation,comparison={'baseline':[{'rule':x.rule,'status':x.status,'finding_id':x.id} for x in all_findings]})
    db.add(t);db.flush();r.status='ready_for_retest';audit(db,u,'remediation.change_recorded',t.id,r.org_id);db.commit()
    return {'id':t.id,'status':t.status,'statement':'Engineer-supplied evidence recorded; AEGIS has not applied or verified a fix.'}

class RetestApproval(BaseModel):
    authorization_id:str
    accepted:bool

@router.post('/retests/{retest_id}/approve')
def approve_retest(retest_id:str,data:RetestApproval,u=Depends(current),db=Depends(database)):
    t=db.scalar(select(Retest).where(Retest.id==retest_id).with_for_update())
    if not t:raise HTTPException(404,'Retest not found.')
    member(db,u,t.org_id,roles=['owner','admin'])
    if not data.accepted or t.status!='awaiting_approval':raise HTTPException(409,'Explicit customer approval of pending change is required.')
    baseline=db.get(Job,t.baseline_job_id)
    a=db.get(Asset,baseline.asset_id)
    baseline_auth=db.get(Authorization,baseline.authorization_id)
    proposed=db.get(Authorization,data.authorization_id)
    if not proposed or proposed.asset_id!=a.id or proposed.scope.get('paths')!=baseline_auth.scope.get('paths'):
        raise HTTPException(409,'Full reassessment requires explicit authorization for all baseline paths.')
    if (proposed.scope.get('type')=='api-response-configuration') != (baseline_auth.scope.get('type')=='api-response-configuration'):
        raise HTTPException(409,'Reassessment must preserve the baseline API or website profile.')
    try:job=enqueue(db,a,data.authorization_id)
    except ValueError as exc:raise HTTPException(409,str(exc))
    t.job_id=job.id;t.approved_by=u.id;t.status='queued';audit(db,u,'remediation.full_retest_approved',t.id,t.org_id);db.commit()
    try:dispatch_outbox.delay()
    except Exception:pass # Durable outbox remains pending; scheduler retries.
    return {'job_id':job.id,'status':'queued','profile':'complete applicable approved non-destructive profile','payment_required':False}

@router.post('/remediations/{request_id}/propose-patch')
def propose_patch(request_id:str,u=Depends(current),db=Depends(database)):
    fix_for(db,u,request_id,['owner','admin','engineer'])
    raise HTTPException(409,'No authorized repository connection exists. No patch generated, tested, approved or applied; use the engineer-managed plan.')


@router.get('/intelligence/rules')
def rules(u=Depends(current),db=Depends(database)):
    from ..checks import RULES
    from ..detectors import CATALOG,active
    candidates=[]
    for key,definition in CATALOG.items():
        r=db.get(DetectionRule,key)
        candidates.append({'key':key,'title':definition['title'],'version':definition['version'],'enabled':active(r),'approved_at':r.approved_at if r else None,'test_evidence':r.test_evidence if r else None})
    return {'built_in':[{'key':r,'version':('2' if r in ('csp.inline','header.frame') else '1'),'status':'bundled; fixture-tested'} for r in RULES], 'candidates':candidates}

@router.post('/admin/intelligence/rules/{rule_key}/validate')
def validate_rule(rule_key:str,u=Depends(current),db=Depends(database)):
    admin(u)
    from ..detectors import CATALOG,validate
    if rule_key not in CATALOG:raise HTTPException(422,'Only code-shipped detectors can be validated; executable feed rules are forbidden.')
    r=db.get(DetectionRule,rule_key)
    version=CATALOG[rule_key]['version']
    if not r:r=DetectionRule(key=rule_key,version=version);db.add(r);db.flush()
    if r.version!=version:r.enabled=False;r.approved_by=None;r.approved_at=None;r.version=version
    try:count=validate(rule_key)
    except ValueError:
        r.enabled=False;r.approved_by=None;r.approved_at=None;r.test_evidence=None
        audit(db,u,'detector.validation_failed',r.key);db.commit()
        raise HTTPException(409,'Code-owned fixture validation failed; activation refused.')
    r.test_evidence=json.dumps({'version':version,'tests':count,'result':'passed','fixture':'code-owned response observations','time':time.time()})
    audit(db,u,'detector.validated',r.key);db.commit();return {'key':r.key,'tests':count,'enabled':r.enabled}

@router.post('/admin/intelligence/rules/{rule_key}/approve')
def approve_rule(rule_key:str,u=Depends(current),db=Depends(database)):
    from ..detectors import evidence_valid
    admin(u);r=db.get(DetectionRule,rule_key)
    if not evidence_valid(r):raise HTTPException(409,'The current code-shipped detector version must pass its fixtures before approval.')
    r.approved_by=u.id;r.approved_at=time.time();r.enabled=True;audit(db,u,'detector.approved',r.key);db.commit()
    return {'key':r.key,'enabled':True,'version':r.version}

@router.post('/admin/intelligence/rules/{rule_key}/disable')
def disable_rule(rule_key:str,u=Depends(current),db=Depends(database)):
    admin(u);r=db.get(DetectionRule,rule_key)
    if not r:raise HTTPException(404,'Detector record not found.')
    r.enabled=False;audit(db,u,'detector.disabled',r.key);db.commit();return {'key':r.key,'enabled':False}
