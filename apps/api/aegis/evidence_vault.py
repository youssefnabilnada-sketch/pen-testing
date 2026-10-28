"""Report integrity ledger. Hashes detect drift, not compromise of the whole database."""
import hashlib,json,time
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from .auth import current,member,audit
from .db import database
from .models import Report,EvidenceSeal,EvidenceLegalHold
router=APIRouter(tags=['Evidence Vault'])
def encoded(snapshot):return json.dumps(snapshot,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def seal(db,report):
    db.add(EvidenceSeal(report_id=report.id,sha256=hashlib.sha256(encoded(report.snapshot)).hexdigest()))
def integrity(db,report):
    s=db.scalar(select(EvidenceSeal).where(EvidenceSeal.report_id==report.id))
    return 'legacy_unsealed' if not s else 'verified' if hashlib.sha256(encoded(report.snapshot)).hexdigest()==s.sha256 else 'mismatch'
def require_integrity(db,report):
    if integrity(db,report)=='mismatch':raise HTTPException(409,'Evidence integrity mismatch; report export blocked.')

class LegalHoldRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=500)

def _report_for_hold(db, report_id, user, *, lock=True):
    # Lock the report to serialize concurrent hold/release actions on PostgreSQL.
    statement = select(Report).where(Report.id == report_id)
    report = db.scalar(statement.with_for_update() if lock else statement)
    if not report:
        raise HTTPException(404, 'Evidence not found.')
    member(db, user, report.org_id, roles=['owner', 'admin'])
    return report

def _active_hold(db, report_id):
    return db.scalar(select(EvidenceLegalHold).where(
        EvidenceLegalHold.report_id == report_id,
        EvidenceLegalHold.released_at.is_(None)).order_by(EvidenceLegalHold.created.desc()))

@router.post('/evidence-vault/{report_id}/legal-hold')
def place_legal_hold(report_id: str, data: LegalHoldRequest, u=Depends(current), db=Depends(database)):
    report = _report_for_hold(db, report_id, u)
    if _active_hold(db, report_id):
        raise HTTPException(409, 'An active preservation hold already exists.')
    hold = EvidenceLegalHold(report_id=report_id, reason=data.reason.strip(), placed_by=u.id)
    if len(hold.reason) < 8:
        raise HTTPException(422, 'Give a meaningful legal hold reason.')
    db.add(hold)
    audit(db, u, 'evidence.legal_hold_placed', report_id, report.org_id)
    db.commit()
    return {'id': hold.id, 'active': True, 'created': hold.created,
            'note': 'Evidence is already retained; this hold prevents future automated retention removal.'}

@router.post('/evidence-vault/{report_id}/legal-hold/release')
def release_legal_hold(report_id: str, data: LegalHoldRequest, u=Depends(current), db=Depends(database)):
    report = _report_for_hold(db, report_id, u)
    hold = _active_hold(db, report_id)
    if not hold:
        raise HTTPException(404, 'No active legal hold exists.')
    reason = data.reason.strip()
    if len(reason) < 8:
        raise HTTPException(422, 'Give a meaningful release reason.')
    hold.released_at = time.time()
    hold.released_by = u.id
    hold.release_reason = reason
    audit(db, u, 'evidence.legal_hold_released', report_id, report.org_id)
    db.commit()
    return {'id': hold.id, 'active': False, 'released_at': hold.released_at,
            'note': 'Releasing a hold does not delete reports or authorize future deletion.'}

@router.get('/evidence-vault/{report_id}/legal-holds')
def legal_hold_history(report_id: str, u=Depends(current), db=Depends(database)):
    report = _report_for_hold(db, report_id, u, lock=False)
    rows = db.scalars(select(EvidenceLegalHold).where(EvidenceLegalHold.report_id == report_id)
                      .order_by(EvidenceLegalHold.created.desc()).limit(100)).all()
    return {'report_id': report.id, 'items': [
        {'id': row.id, 'created': row.created, 'reason': row.reason,
         'placed_by': row.placed_by, 'released_at': row.released_at,
         'released_by': row.released_by, 'release_reason': row.release_reason} for row in rows]}

@router.get('/organizations/{org_id}/evidence-vault')
def listing(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id)
    rows=db.scalars(select(Report).where(Report.org_id==org_id).order_by(Report.created.desc()).limit(100))
    selected = rows.all()
    ids = [r.id for r in selected]
    held = set(db.scalars(select(EvidenceLegalHold.report_id).where(
        EvidenceLegalHold.report_id.in_(ids), EvidenceLegalHold.released_at.is_(None))).all()) if ids else set()
    return {'retention':'Retained until an explicitly authorized operator retention procedure. No automatic deletion.',
        'integrity_limit':'Database hashes are not independent notarization or protection against complete database compromise.',
        'items':[{'id':r.id,'job_id':r.job_id,'created':r.created,'integrity':integrity(db,r),'profile':r.snapshot.get('profile',{}).get('version'), 'legal_hold':r.id in held} for r in selected]}

@router.get('/evidence-vault/{report_id}/export')
def export(report_id:str,u=Depends(current),db=Depends(database)):
    r=db.get(Report,report_id)
    if not r:raise HTTPException(404,'Evidence not found.')
    member(db,u,r.org_id);require_integrity(db,r)
    payload={'report':r.snapshot,'sha256':hashlib.sha256(encoded(r.snapshot)).hexdigest(),'integrity':integrity(db,r),'format':'aegis-evidence-v1'}
    audit(db,u,'evidence.exported',r.id,r.org_id);db.commit()
    return Response(json.dumps(payload,ensure_ascii=False),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="aegis-evidence-{r.id}.json"','Cache-Control':'no-store'})
