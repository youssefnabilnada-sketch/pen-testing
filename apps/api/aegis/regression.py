"""Complete supported profile, with explicit not-tested classifications."""
import time
from http.cookies import SimpleCookie
from sqlalchemy import select
from .checks import RULES, analyze
from .models import DetectionRule, Retest, Remediation, Finding, FindingHistory, AdvisoryImpact, InventoryItem
from .intelligence.service import notify

PROFILE_VERSION='root-response-configuration-v3'
CANDIDATE_RULE='header.referrer'


def profile(db,origin,response):
    observations=analyze(origin,response)
    headers={k.lower():v for k,v in response.headers}
    executed=set(RULES)
    unverified={}
    from .policies import single_csp
    csp_present=any(k.lower()=='content-security-policy' and v.strip() for k,v in response.headers)
    if csp_present and single_csp(response.headers) is None:
        for rule in ('csp.inline','header.frame'):
            executed.discard(rule);unverified[rule]='Multiple CSP policies require browser intersection analysis; no verified-fix conclusion.'
    if not origin.startswith('https:'):
        for rule in ('header.hsts','hsts.short','tls.expiry'):
            executed.discard(rule);unverified[rule]='HTTPS was not in this authorized origin.'
    elif not response.tls:
        executed.discard('tls.expiry');unverified['tls.expiry']='No validated TLS certificate evidence.'
    if not csp_present:
        executed.discard('csp.inline');unverified['csp.inline']='CSP is absent; previous script policy cannot be validated.'
    cookies=False;unparseable=False
    for name,value in response.headers:
        if name.lower()=='set-cookie':
            jar=SimpleCookie()
            try:
                jar.load(value);cookies=cookies or bool(jar)
                if not jar:unparseable=True
            except Exception:unparseable=True
    if not cookies or unparseable:
        for rule in ('cookie.secure','cookie.httponly'):
            executed.discard(rule);unverified[rule]='No parseable Set-Cookie in this response; earlier cookies are not proven fixed.'
    from .detectors import CATALOG,evaluate,active
    versions={r:('2' if r in ('csp.inline','header.frame') else '1') for r in executed}
    for key,definition in CATALOG.items():
        candidate=db.get(DetectionRule,key)
        if not active(candidate):continue
        observation,reason=evaluate(key,response)
        if reason:unverified[key]=reason;continue
        executed.add(key);versions[key]=definition['version']
        if observation:observations.append(observation)
    return observations,{'version':PROFILE_VERSION,'executed':sorted(executed),'not_performed':unverified,'rule_versions':{r:versions[r] for r in sorted(executed)}}



def compare(baseline,observations,manifest):
    before={f['rule']:f for f in baseline};after={f['rule']:f for f in observations};executed=set(manifest['executed'])
    return {'resolved':sorted(r for r in before if r not in after and r in executed),
        'unresolved':sorted(set(before)&set(after)),
        'new':sorted(set(after)-set(before)),
        'unverified':[{'rule':r,'reason':manifest['not_performed'].get(r,'No approved safe detector was executed for this previous observation.')} for r in sorted(before) if r not in executed],
        'profile':manifest,'assurance':'Complete applicable supported safe profile only; not a comprehensive penetration test or proof of absence of vulnerabilities.'}


def advisory_evaluation(db,asset_id):
    ids=list(db.scalars(select(InventoryItem.id).where(InventoryItem.asset_id==asset_id)))
    return [{'advisory_id':i.advisory_id,'status':i.status,'verification':'unverified runtime impact; no advisory-specific detector','reason':i.reason,'revision_ids':i.revision_ids} for i in db.scalars(select(AdvisoryImpact).where(AdvisoryImpact.inventory_id.in_(ids),AdvisoryImpact.status.in_(['potential','confirmed_inventory_match'])))]


def finish_retest(db,job,observations,manifest):
    retest=db.scalar(select(Retest).where(Retest.job_id==job.id))
    if not retest:return None
    comparison=compare(retest.comparison['baseline'],observations,manifest)
    comparison['advisories']=advisory_evaluation(db,job.asset_id)
    original=db.get(Finding,db.get(Remediation,retest.remediation_id).finding_id)
    if original.rule in {o['rule'] for o in observations}:
        retest.status='failed_verification';original.status='reopened'
        db.add(FindingHistory(finding_id=original.id,job_id=job.id,status='reopened'))
        comparison['original']='still_detected'
    elif original.rule in manifest['executed']:
        retest.status='verified_original';comparison['original']='not_detected_by_supported_check'
    else:retest.status='unverified';comparison['original']='not_tested'
    comparison['baseline_job_id']=retest.baseline_job_id
    comparison['completed_at']=time.time()
    retest.comparison=comparison
    notify(db,job.org_id,'remediation_retest','retest:'+retest.id,'Remediation reassessment: '+retest.status, 'Resolved: '+str(len(comparison['resolved']))+'; unresolved: '+str(len(comparison['unresolved']))+'; new: '+str(len(comparison['new']))+'; unverified: '+str(len(comparison['unverified']))+'. No guarantee of overall security.',retest.remediation_id)
    return comparison
