import hashlib
import json
import re
import time
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet, InvalidSpecifier
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from ..db import Session
from ..models import IntelligenceSource, SyncRun, Advisory, AdvisoryAlias, KnowledgeRevision, InventoryItem, AdvisoryImpact, Notification, AssessmentSchedule
from .feeds import SOURCES, record, collect, FeedError


def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def notify(db,org,kind,key,title,detail,target):
    if not db.scalar(select(Notification).where(Notification.org_id==org,Notification.dedupe_key==key)):
        row=Notification(org_id=org,kind=kind,dedupe_key=key,title=title,detail=detail,target=target)
        db.add(row);db.flush()
        from ..email_alerts import queue_alert
        queue_alert(db,row)


def ensure_sources(db):
    for key in SOURCES:
        if not db.get(IntelligenceSource,key):
            try:
                with db.begin_nested():
                    db.add(IntelligenceSource(key=key));db.flush()
            except IntegrityError:pass
    db.flush()


def ingest(db,source,records):
    if source not in SOURCES:raise FeedError('Unapproved source')
    changed=[]
    for incoming in records:
        data=record(incoming);aliases=data['identifiers']
        matches=set(db.scalars(select(AdvisoryAlias.advisory_id).where(AdvisoryAlias.alias.in_(aliases))))
        if len(matches)>1:raise FeedError('Conflicting alias graph requires human merge review')
        a=db.get(Advisory,next(iter(matches))) if matches else None
        canonical=next((x for x in aliases if x.startswith('CVE-')),aliases[0])
        if not a:
            a=Advisory(identifier=canonical,title=data['title']);db.add(a);db.flush()
        elif canonical.startswith('CVE-') and not a.identifier.startswith('CVE-'):a.identifier=canonical
        for alias in aliases:
            if not db.get(AdvisoryAlias,alias):db.add(AdvisoryAlias(alias=alias,advisory_id=a.id))
        fingerprint=digest(data)
        current=db.scalar(select(KnowledgeRevision).where(KnowledgeRevision.advisory_id==a.id,KnowledgeRevision.source==source,KnowledgeRevision.current.is_(True)))
        if current and current.digest==fingerprint:continue
        if current:current.current=False
        existing=db.scalar(select(KnowledgeRevision).where(KnowledgeRevision.advisory_id==a.id,KnowledgeRevision.source==source,KnowledgeRevision.digest==fingerprint))
        if existing:
            existing.current=True
            # Returning to prior data does not silently retain an approval from a later epoch.
            existing.approved_by=None;existing.approved_at=None
        else:
            existing=KnowledgeRevision(advisory_id=a.id,source=source,digest=fingerprint,content=data,source_updated=data['modified']);db.add(existing)
        a.title=data['title'];a.updated=time.time();db.flush()
        revisions=db.scalars(select(KnowledgeRevision).where(KnowledgeRevision.advisory_id==a.id,KnowledgeRevision.current.is_(True))).all()
        a.exploited=any(r.source=='cisa' and r.content['exploited'] and not r.content['withdrawn'] for r in revisions)
        rank=['unknown','low','medium','high','critical']
        a.severity=max((r.content['severity'] for r in revisions if not r.content['withdrawn']),key=rank.index,default='unknown')
        changed.append(a.id)
    db.flush()
    return set(changed)


def normalize_name(ecosystem,name):
    return re.sub(r'[-_.]+','-',name).lower() if ecosystem=='PyPI' else name.lower() if ecosystem in ('npm','vendor','cpe') else name


def version_match(item,affected):
    """True = declared inventory satisfies supported affected versions, not exploitability."""
    if not item.version:return None
    if item.ecosystem=='cpe' and affected.get('name')=='php:php':
        from .php_versions import match_php_cpe
        return match_php_cpe(item.version,affected)
    if item.version in affected.get('versions',[]):return True
    try:
        if item.ecosystem=='npm' and not re.fullmatch(r'\d+\.\d+\.\d+',item.version):return None
        v=Version(item.version)
        expression=affected.get('range')
        if expression:
            if item.ecosystem not in ('PyPI','npm'):return None
            groups=expression.split('||')
            result=False
            for group in groups:
                group=group.strip()
                if item.ecosystem=='npm' and not re.fullmatch(r'(?:[<>=!]{1,2}\s*\d+\.\d+\.\d+)(?:\s*,\s*[<>=!]{1,2}\s*\d+\.\d+\.\d+)*',group):return None
                group=re.sub(r'(?<![<>=!])=(?!=)','==',group)
                result=result or SpecifierSet(group).contains(v,prereleases=True)
            return result
        ranges=affected.get('ranges',[])
        supported=False
        unsupported=False
        for rg in ranges:
            if rg['type']!='SEMVER' or item.ecosystem not in ('npm','PyPI'):
                unsupported=True
                continue
            # Preserve OSV SEMVER semantics only for stable x.y.z values.
            if not re.fullmatch(r'\d+\.\d+\.\d+',item.version):return None
            lower=None
            for event in rg['events']:
                if 'introduced' in event:
                    raw=event['introduced'];lower=Version('0.0.0') if raw=='0' else Version(raw)
                else:
                    key=next((k for k in ('fixed','last_affected','limit') if k in event),None)
                    if not key or lower is None:return None
                    upper=Version(event[key]);supported=True
                    if lower<=v and (v<=upper if key=='last_affected' else v<upper):return True
                    lower=None
            if lower is not None:
                supported=True
                if lower<=v:return True
        if supported:return None if unsupported else False
        # Lists may be incomplete if unsupported range semantics also exist.
        if affected.get('versions') and not ranges:return False
    except (InvalidVersion,InvalidSpecifier,KeyError,TypeError):return None
    return None


def match_inventory(db,org_id=None):
    query=select(InventoryItem)
    if org_id:query=query.where(InventoryItem.org_id==org_id)
    items=db.scalars(query).all()
    revisions=db.scalars(select(KnowledgeRevision).where(KnowledgeRevision.current.is_(True))).all()
    by_advisory={}
    for r in revisions:by_advisory.setdefault(r.advisory_id,[]).append(r)
    for item in items:
        existing={x.advisory_id:x for x in db.scalars(select(AdvisoryImpact).where(AdvisoryImpact.inventory_id==item.id))}
        touched=set()
        for aid,versions in by_advisory.items():
            candidates=[]
            for r in versions:
                if r.content['withdrawn']:continue
                for aff in r.content['affected']:
                    if aff.get('ecosystem')==item.ecosystem and normalize_name(item.ecosystem,aff.get('name',''))==normalize_name(item.ecosystem,item.package):
                        candidates.append((version_match(item,aff),r.id))
            if not candidates:continue
            touched.add(aid)
            # Contradictory sources never become a confirmed inventory match.
            flags={x[0] for x in candidates}
            status='confirmed_inventory_match' if True in flags and False not in flags else 'not_affected_by_inventory' if flags=={False} else 'potential'
            reason={'confirmed_inventory_match':'Declared package/version matches an official affected-version statement. Runtime presence and exploitability are not verified.', 'potential':'Product matches, but missing/unsupported version semantics or conflicting sources require review. This is not a confirmed vulnerability.', 'not_affected_by_inventory':'Declared version does not match the supported affected ranges. This does not verify a deployed fix.'}[status]
            revision_ids=sorted(set(x[1] for x in candidates))
            impact=existing.get(aid)
            changed=not impact or impact.status!=status or impact.revision_ids!=revision_ids
            if not impact:
                impact=AdvisoryImpact(org_id=item.org_id,inventory_id=item.id,advisory_id=aid,status=status,reason=reason,revision_ids=revision_ids);db.add(impact)
            else:impact.status=status;impact.reason=reason;impact.revision_ids=revision_ids;impact.updated=time.time()
            if changed and status!='not_affected_by_inventory':
                a=db.get(Advisory,aid)
                key='advisory:'+digest([item.id,item.version,aid,status,revision_ids])
                notify(db,item.org_id,'advisory_impact',key,a.identifier+' may affect your inventory',reason,item.asset_id)
                schedule=db.scalar(select(AssessmentSchedule).where(AssessmentSchedule.asset_id==item.asset_id,AssessmentSchedule.enabled.is_(True),AssessmentSchedule.on_advisory.is_(True)))
                if schedule:schedule.next_due=min(schedule.next_due,time.time())
        for aid,impact in existing.items():
            if aid not in touched and impact.status!='withdrawn_or_no_match':
                impact.status='withdrawn_or_no_match';impact.updated=time.time();impact.reason='Current source data no longer supports this inventory match; this is not evidence of a fixed runtime vulnerability.'
    db.flush()


def synchronize(source,transport=None,pause=None):
    now=time.time()
    with Session() as db:
        ensure_sources(db);db.commit()
        claimed=db.execute(update(IntelligenceSource).where(IntelligenceSource.key==source,IntelligenceSource.enabled.is_(True),IntelligenceSource.lease_until<now).values(lease_until=now+600,last_attempt=now))
        db.commit()
        if not claimed.rowcount:return {'status':'already_running_or_disabled'}
        for abandoned in db.scalars(select(SyncRun).where(SyncRun.source==source,SyncRun.status=='running')):
            abandoned.status='failed';abandoned.finished=now;abandoned.error='Worker lease expired; retry started without advancing source checkpoint.'
        s=db.get(IntelligenceSource,source);run=SyncRun(source=source);db.add(run);db.commit();run_id=run.id
        try:
            kwargs={}
            if transport is not None:kwargs['transport']=transport
            if pause is not None:kwargs['pause']=pause
            ids=list(db.scalars(select(AdvisoryAlias.alias)))
            data,cursor=collect(source,s.cursor,now,ids,**kwargs)
            # Release read transaction during network and use current state again.
            ingest(db,source,data);match_inventory(db)
            s.cursor=cursor;s.last_success=now;s.next_due=now+s.interval_hours*3600;s.failures=0;s.error=None;s.lease_until=0
            run.status='completed';run.records=len(data);run.finished=time.time();db.commit()
            return {'status':'completed','records':len(data)}
        except Exception as exc:
            db.rollback();s=db.get(IntelligenceSource,source);run=db.get(SyncRun,run_id)
            s.failures+=1;s.next_due=now+min(3600,60*2**min(s.failures-1,6));s.lease_until=0
            # Do not include source payloads, secrets or remote error bodies in logs/UI.
            s.error=type(exc).__name__+': source update failed; previous successful knowledge retained.'
            run.status='failed';run.finished=time.time();run.error=s.error;db.commit()
            return {'status':'failed','error':s.error}


def retrieve(db,query,limit=8):
    words={w.lower() for w in re.findall(r'[A-Za-z0-9_.-]+',query) if len(w)>2}
    candidates=[]
    for r in db.scalars(select(KnowledgeRevision).where(KnowledgeRevision.current.is_(True),KnowledgeRevision.approved_at.is_not(None))):
        if r.content['withdrawn']:continue
        haystack=json.dumps({'identifiers':r.content['identifiers'],'title':r.content['title'],'affected':r.content['affected']}).lower()
        score=sum(w in haystack for w in words)
        if score:candidates.append((score,r))
    candidates.sort(key=lambda x:(x[0],x[1].created),reverse=True)
    return [{'revision_id':r.id,'source':r.source,'approved_at':r.approved_at,'data':r.content} for _,r in candidates[:limit]]


def grounded_guidance(db,query):
    context=retrieve(db,query)
    return {'mode':'retrieval-augmented deterministic synthesis; no model weights retrained',
        'answer':'Review the approved source-backed remediation and compatibility notes below.' if context else 'No approved matching knowledge is available. Do not infer that no advisory exists.',
        'evidence':context,
        'plan':{'compatibility':'Review release notes, API changes, runtime constraints and transitive dependencies before upgrading.',
            'effort':'Preliminary; engineer review required. Inventory match alone is insufficient to estimate deployment effort.',
            'deployment_gate':'Customer approval, authorized access, backup/rollback plan and staging tests required. AEGIS does not deploy production changes.',
            'required_testing':['Original observation','All supported previous observations','Complete applicable safe assessment profile','Dependency and application regression tests in authorized staging'],
            'verification_limit':'Advisory matches without an approved safe runtime detector remain unverified after HTTP configuration retesting.'}}
