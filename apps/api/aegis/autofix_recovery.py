"""Backup integrity and isolated restore rehearsal. No repository scripts execute."""
import hashlib,json,tempfile,difflib
from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from .auth import current,member,audit
from .db import database
from .models import PatchBackup,RepositoryPatch,Remediation,Finding,Job,Report,Asset,Authorization
from . import github_client as gh
router=APIRouter(tags=['AutoFix recovery'])

def restore_rehearsal(ciphertext,sha256,proposed):
    original=gh.cipher().decrypt(ciphertext.encode())
    if hashlib.sha256(original).hexdigest()!=sha256:raise ValueError('Backup integrity mismatch.')
    if not isinstance(json.loads(original),dict):raise ValueError('Backup is not a JSON object.')
    with tempfile.TemporaryDirectory(prefix='aegis-restore-') as directory:
        target=Path(directory)/'vercel.json'
        target.write_bytes(proposed.encode());target.write_bytes(original)
        if target.read_bytes()!=original:raise ValueError('Restore rehearsal failed.')
    return original

def create_backup(db,patch,original,proposed):
    encrypted=gh.cipher().encrypt(original.encode()).decode();digest=hashlib.sha256(original.encode()).hexdigest()
    restore_rehearsal(encrypted,digest,proposed)
    db.add(PatchBackup(patch_id=patch.id,encrypted_content=encrypted,sha256=digest,restore_verified=True))
    patch.test_evidence={**patch.test_evidence,'backup_sha256':digest,'restore_rehearsal':'isolated byte-for-byte restoration passed','backup_scope':'vercel.json only; not database or whole-site backup'}

@router.post('/repository-patches/{patch_id}/rollback-preview')
def rollback_preview(patch_id:str,u=Depends(current),db=Depends(database)):
    p=db.get(RepositoryPatch,patch_id)
    if not p:raise HTTPException(404,'Proposal not found.')
    member(db,u,p.org_id,roles=['owner','admin'])
    backup=db.scalar(select(PatchBackup).where(PatchBackup.patch_id==patch_id))
    if not backup:raise HTTPException(409,'No verified original backup exists for this proposal.')
    try:
        proposed=gh.cipher().decrypt(p.proposed_content.encode()).decode()
        original=restore_rehearsal(backup.encrypted_content,backup.sha256,proposed).decode()
    except Exception as exc:raise HTTPException(409,'Backup verification failed. No rollback authorized or applied.') from exc
    diff=''.join(difflib.unified_diff(proposed.splitlines(True),original.splitlines(True),fromfile='proposed/vercel.json',tofile='restored/vercel.json'))
    audit(db,u,'autofix.rollback_previewed',p.id,p.org_id);db.commit()
    return {'diff':diff,'backup_sha256':backup.sha256,'restore_verified':True,'applied':False,'warning':'Review current repository state before applying rollback; later changes must not be overwritten.'}

class StagingInput(BaseModel):
    job_id:str
    accepted:bool

@router.post('/repository-patches/{patch_id}/staging-evidence')
def staging(patch_id:str,data:StagingInput,u=Depends(current),db=Depends(database)):
    p=db.get(RepositoryPatch,patch_id)
    if not p:raise HTTPException(404,'Proposal not found.')
    member(db,u,p.org_id,roles=['owner','admin'])
    if not data.accepted:raise HTTPException(403,'Explicit staging evidence linkage required.')
    remediation=db.get(Remediation,p.remediation_id)
    if not remediation or remediation.org_id!=p.org_id:
        raise HTTPException(409,'Original remediation is unavailable for this workspace.')
    finding=db.get(Finding,remediation.finding_id)
    if not finding or finding.org_id!=p.org_id:
        raise HTTPException(409,'Original finding is unavailable for this workspace.')
    job=db.get(Job,data.job_id)
    if (not job or job.org_id!=p.org_id or job.asset_id==finding.asset_id
        or job.created<p.created or job.status!='completed'):
        raise HTTPException(409,'Use a new completed assessment on a separate staging asset in this workspace.')
    report=db.scalar(select(Report).where(Report.job_id==job.id))
    baseline=db.get(Job,finding.job_id)
    if (not report or report.org_id!=p.org_id or not baseline
        or baseline.org_id!=p.org_id or baseline.asset_id!=finding.asset_id):
        raise HTTPException(409,'Baseline or staging report evidence is unavailable.')
    baseline_auth=db.get(Authorization,baseline.authorization_id)
    staging_auth=db.get(Authorization,job.authorization_id)
    if (not baseline_auth or not staging_auth or baseline_auth.asset_id!=baseline.asset_id
        or staging_auth.asset_id!=job.asset_id):
        raise HTTPException(409,'Assessment authorization evidence is unavailable.')
    expected=baseline_auth.scope.get('paths') if isinstance(baseline_auth.scope,dict) else None
    scope=staging_auth.scope
    if (not isinstance(scope,dict) or not isinstance(expected,list)
        or scope.get('paths')!=expected or scope.get('type')=='api-response-configuration'):
        raise HTTPException(409,'Staging must assess every baseline website path.')
    from .multipath import qualify
    from .staging_evidence import evaluate_staging
    rules={qualify('header.nosniff',path) for path in expected}
    try:
        passed=evaluate_staging(report.snapshot,expected,rules)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc
    p.test_evidence={**p.test_evidence,'staging':{'job_id':job.id,'supported_checks_passed':passed,'deployment_revision_verified':False,'scope':scope['paths'],'statement':'Observed staging response only; repository commit deployment and application behavior require separate validation.'}}
    audit(db,u,'autofix.staging_evidence_linked',p.id,p.org_id);db.commit()
    return p.test_evidence['staging']
