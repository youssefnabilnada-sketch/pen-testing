"""Read-only release evidence pinned to one authorized GitHub PR head."""
import re
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel,Field
from sqlalchemy import select
from .auth import current,member,audit
from .db import database
from .models import LaunchReview
from .repositories import connection,repo_path,call
router=APIRouter(tags=['Launch Guard'])
class ReviewInput(BaseModel):
    connection_id:str
    repository:str=Field(max_length=220)
    pull_request:int=Field(ge=1,le=10000000,strict=True)
    accepted:bool

def mapping(value):
    if not isinstance(value,dict):raise HTTPException(502,'Malformed release evidence.')
    return value

def rows(value,key):
    value=mapping(value);items=value.get(key);count=value.get('total_count')
    if not isinstance(items,list) or len(items)>100 or any(not isinstance(r,dict) for r in items) or type(count) is not int or count<0:
        raise HTTPException(502,'Malformed release evidence.')
    return items

def revision(pr,repository):
    head=mapping(mapping(pr).get('head'));sha=head.get('sha')
    name=mapping(head.get('repo')).get('full_name')
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{40}',sha) or not isinstance(name,str) or name.lower()!=repository.lower():
        raise HTTPException(422,'Use a same-repository PR with a valid immutable commit. Fork review is not supported.')
    return sha

def change_review_categories(path):
    """Conservative, path-only change indicators; never claim a dependency audit."""
    path=path.lower().replace('\\', '/')
    basename=path.rsplit('/', 1)[-1]
    result=[]
    if (basename in {'package.json','package-lock.json','pnpm-lock.yaml','yarn.lock',
                     'poetry.lock','uv.lock','pipfile','pipfile.lock','go.mod','go.sum',
                     'pyproject.toml','cargo.toml','cargo.lock','composer.json','composer.lock'}
        or re.fullmatch(r'requirements[^/]*\.(?:txt|in)',basename)):
        result.append('dependency_manifest_review')
    if (basename in {'dockerfile','docker-compose.yml','docker-compose.yaml','vercel.json'}
        or basename.endswith('.tf') or path.startswith('infrastructure/deployment/')):
        result.append('deployment_configuration_review')
    if path.startswith('.github/workflows/'):
        result.append('ci_workflow_review')
    if path.startswith(('apps/api/aegis/auth.py','apps/api/aegis/mfa.py',
                        'apps/api/aegis/safety.py','apps/api/aegis/scope.py')):
        result.append('security_boundary_review')
    if path.startswith('apps/api/migrations/versions/'):
        result.append('database_migration_review')
    return result

def summarize(checks,statuses,files):
    runs=rows(checks,'check_runs');contexts=rows(statuses,'statuses')
    if not isinstance(files,list) or len(files)>100 or any(not isinstance(f,dict) or not isinstance(f.get('filename'),str) or len(f['filename'])>500 for f in files):raise HTTPException(502,'Malformed release evidence.')
    complete=checks.get('total_count')==len(runs) and statuses.get('total_count')==len(contexts) and len(files)<100
    all_green=bool(runs or contexts) and all(r.get('status')=='completed' and r.get('conclusion')=='success' for r in runs) and all(r.get('state')=='success' for r in contexts)
    changed=[{'path':f['filename'][:500], 'status':str(f.get('status','unknown'))[:30],
              'review_required':bool(change_review_categories(f['filename'])),
              'review_categories':change_review_categories(f['filename'])} for f in files[:100]]
    categories=sorted({name for f in changed for name in f['review_categories']})
    return {'ci':'passed' if complete and all_green else 'incomplete_or_not_passed','evidence_complete':complete,
            'checks':[{'name':str(r.get('name',''))[:200],'status':r.get('status'),'conclusion':r.get('conclusion')} for r in runs[:100]],
            'statuses':[{'name':str(r.get('context',''))[:200],'state':r.get('state')} for r in contexts[:100]],
            'changed_files':changed,'required_reviews':categories,
            'staging':'not_run',
            'dependency_analysis':'changed manifests flagged for human review; no dependency audit executed',
            'dependency_audit':'not_performed', 'release_gate':'advisory_only','certification':False}

@router.post('/launch-reviews')
def review(data:ReviewInput,u=Depends(current),db=Depends(database)):
    if not data.accepted:raise HTTPException(403,'Explicit read-only release-review consent required.')
    c,token=connection(db,u,data.connection_id)
    member(db,u,c.org_id,roles=['owner','admin','analyst'])
    base=repo_path(data.repository)
    metadata=mapping(call(base,token))
    if mapping(metadata.get('permissions')).get('pull') is not True:raise HTTPException(403,'Repository read permission required.')
    pr=call(base+'/pulls/'+str(data.pull_request),token)
    sha=revision(pr,data.repository)
    files=call(base+'/pulls/'+str(data.pull_request)+'/files?per_page=100',token)
    checks=call(base+'/commits/'+sha+'/check-runs?per_page=100&filter=latest',token)
    statuses=call(base+'/commits/'+sha+'/status?per_page=100',token)
    result=summarize(checks,statuses,files)
    latest=call(base+'/pulls/'+str(data.pull_request),token)
    if revision(latest,data.repository)!=sha:raise HTTPException(409,'PR changed during review. Start a new review.')
    db.expire_all();connection(db,u,data.connection_id)
    member(db,u,c.org_id,roles=['owner','admin','analyst'])
    if statuses.get('sha')!=sha or any(r.get('head_sha')!=sha for r in checks.get('check_runs',[])):
        raise HTTPException(502,'CI evidence does not match the approved revision.')
    if type(pr.get('changed_files')) is not int or pr['changed_files']!=len(files):raise HTTPException(422,'Changed-file evidence exceeds the supported page or is incomplete.')
    result['pull_request']=data.pull_request
    previous=db.scalar(select(LaunchReview).where(LaunchReview.org_id==c.org_id,LaunchReview.repository==data.repository).order_by(LaunchReview.created.desc()).limit(1))
    result['previous_revision']=previous.revision if previous else None
    row=LaunchReview(org_id=c.org_id,user_id=u.id,repository=data.repository,revision=sha,result=result)
    db.add(row);db.flush();audit(db,u,'launch.reviewed',row.id,c.org_id);db.commit()
    return {'id':row.id,'revision':sha,'result':result}

@router.get('/organizations/{org_id}/launch-reviews')
def history(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    return [{'id':r.id,'created':r.created,'repository':r.repository,'revision':r.revision,'result':r.result} for r in db.scalars(select(LaunchReview).where(LaunchReview.org_id==org_id).order_by(LaunchReview.created.desc()).limit(50))]


@router.get('/launch-reviews/{review_id}/report.pdf')
def pdf_report(review_id: str, u=Depends(current), db=Depends(database)):
    """Export only the persisted, immutable-revision evidence visible to this tenant."""
    row = db.get(LaunchReview, review_id)
    if not row:
        raise HTTPException(404, 'Launch review not found.')
    member(db, u, row.org_id)
    from .reporting import render_launch_review_pdf
    return Response(render_launch_review_pdf(row).getvalue(), media_type='application/pdf',
                    headers={'Cache-Control': 'no-store',
                             'Content-Disposition': 'attachment; filename="aegis-launch-review.pdf"',
                             'X-Content-Type-Options': 'nosniff'})
