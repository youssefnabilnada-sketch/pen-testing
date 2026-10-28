"""Agency views never confer ordinary client workspace membership."""
import time
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from .auth import current,member,audit
from .db import database
from .models import AgencyGrant,AgencyBrand,Organization,Asset,Finding,Job,Report,HealthMonitor,Remediation
router=APIRouter(tags=['Agency'])
class Delegation(BaseModel):
    agency_id:str
    accepted:bool
    reports:bool=False
    days:int=Field(default=7,ge=1,le=30,strict=True)
class Branding(BaseModel):
    name:str=Field(min_length=2,max_length=100)
    cover:str=Field(default='',max_length=300)
    contact:str=Field(default='',max_length=200)
    color:str=Field(default='#123842',pattern=r'^#[0-9a-fA-F]{6}$')
    logo_png:str=Field(default='',max_length=350000)

@router.put('/organizations/{client_id}/agency-grant')
def grant(client_id:str,data:Delegation,u=Depends(current),db=Depends(database)):
    member(db,u,client_id,roles=['owner'])
    if not data.accepted or data.agency_id==client_id:raise HTTPException(422,'Explicit delegation to another workspace required.')
    if not db.get(Organization,data.agency_id):raise HTTPException(404,'Agency workspace not found.')
    row=db.scalar(select(AgencyGrant).where(AgencyGrant.client_id==client_id,AgencyGrant.agency_id==data.agency_id))
    if not row:row=AgencyGrant(client_id=client_id,agency_id=data.agency_id);db.add(row)
    row.reports=data.reports;row.revoked=False;row.expires=time.time()+data.days*86400
    db.flush();audit(db,u,'agency.delegated',row.id,client_id);db.commit()
    return {'id':row.id,'expires':row.expires}

@router.get('/organizations/{client_id}/agency-grants')
def grants(client_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,client_id,roles=['owner'])
    return [{'id':r.id,'agency_id':r.agency_id,'expires':r.expires,'revoked':r.revoked,'reports':r.reports} for r in db.scalars(select(AgencyGrant).where(AgencyGrant.client_id==client_id))]

@router.delete('/agency-grants/{grant_id}')
def revoke(grant_id:str,u=Depends(current),db=Depends(database)):
    r=db.get(AgencyGrant,grant_id)
    if not r:raise HTTPException(404,'Delegation not found.')
    member(db,u,r.client_id,roles=['owner']);r.revoked=True;audit(db,u,'agency.revoked',r.id,r.client_id);db.commit();return {'revoked':True}

@router.put('/organizations/{org_id}/agency-brand')
def brand(org_id:str,data:Branding,u=Depends(current),db=Depends(database)):
    member(db,u,org_id,roles=['owner','admin'])
    settings=data.model_dump()
    if data.logo_png:
        from .image_evidence import sanitize_png
        try:settings['logo_png'],_=sanitize_png(data.logo_png)
        except Exception as exc:raise HTTPException(422,'Use a valid bounded PNG logo.') from exc
    r=db.scalar(select(AgencyBrand).where(AgencyBrand.org_id==org_id))
    if not r:r=AgencyBrand(org_id=org_id,settings=settings);db.add(r)
    else:r.settings=settings
    audit(db,u,'agency.brand.updated',org_id,org_id);db.commit();return {'saved':True}

@router.get('/organizations/{org_id}/agency-portfolio')
def portfolio(org_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id,roles=['owner','admin','analyst'])
    rows=db.scalars(select(AgencyGrant).where(AgencyGrant.agency_id==org_id,AgencyGrant.revoked.is_(False),AgencyGrant.expires>time.time()).limit(100))
    result=[]
    for r in rows:
        def count(model):return db.scalar(select(func.count()).select_from(model).where(model.org_id==r.client_id))
        result.append({'client_id':r.client_id,'name':db.get(Organization,r.client_id).name,'expires':r.expires,'reports_allowed':r.reports,
            'assets':count(Asset),'findings':count(Finding),'monitors':count(HealthMonitor),'remediations':count(Remediation),
            'assessments':[{'id':j.id,'status':j.status,'created':j.created} for j in db.scalars(select(Job).where(Job.org_id==r.client_id).order_by(Job.created.desc()).limit(20))]})
    return result

@router.get('/organizations/{org_id}/agency-reports/{job_id}')
def report(org_id:str,job_id:str,u=Depends(current),db=Depends(database)):
    member(db,u,org_id,roles=['owner','admin','analyst'])
    job=db.get(Job,job_id)
    if not job:raise HTTPException(404,'Assessment not found.')
    grant=db.scalar(select(AgencyGrant).where(AgencyGrant.agency_id==org_id,AgencyGrant.client_id==job.org_id,AgencyGrant.revoked.is_(False),AgencyGrant.reports.is_(True),AgencyGrant.expires>time.time()))
    if not grant:raise HTTPException(403,'Client report delegation required.')
    snapshot=db.scalar(select(Report).where(Report.job_id==job_id))
    if not snapshot:raise HTTPException(404,'Report not ready.')
    from .evidence_vault import require_integrity
    require_integrity(db,snapshot)
    branding=db.scalar(select(AgencyBrand).where(AgencyBrand.org_id==org_id))
    from .reporting import render_pdf
    audit(db,u,'agency.report.exported',job_id,job.org_id);db.commit()
    return StreamingResponse(render_pdf(snapshot.snapshot,branding.settings if branding else None),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="agency-{job_id}.pdf"','Cache-Control':'no-store'})
