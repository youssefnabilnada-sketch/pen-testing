"""Capability-based verification recommendations; no unconsented network discovery."""
from urllib.parse import urlsplit
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel
from typing import Literal
from sqlalchemy import select
from .auth import current
from .db import database
from .models import Challenge
import time
router=APIRouter(tags=['SmartVerify'])
class Capabilities(BaseModel):
    platform: Literal['auto','cloudflare','vercel','netlify','wordpress','cpanel','plesk','github','other']='auto'
    dns_access: bool=False
    repository_access: bool=False
    html_access: bool=False

def recommend(origin,data):
    host=urlsplit(origin).hostname or ''
    platform=data.platform
    source='customer selection'
    if platform=='auto':
        platform=next((p for suffix,p in [('vercel.app','vercel'),('netlify.app','netlify'),('github.io','github')] if host.endswith('.'+suffix)), 'other')
        source='hostname hint' if platform!='other' else 'unknown; no network detection performed'
    if platform=='wordpress':method='meta';reason='The WordPress plugin can publish the temporary homepage challenge.'
    elif data.dns_access or platform=='cloudflare':method='dns';reason='DNS access allows publishing a TXT proof without changing website content.'
    elif data.repository_access or platform in ('vercel','netlify','github','cpanel','plesk'):method='file';reason='Publish a verification file through your reviewed deployment or hosting workflow.'
    elif data.html_access:method='meta';reason='Your homepage editor can publish the exact meta tag.'
    else:method='dns';reason='Start with DNS; use a verification file or meta tag if you cannot manage DNS.'
    return {'platform':platform,'method':method,'reason':reason,'source':source,'automatic_connection':False,
            'alternatives':[m for m in ('dns','file','meta') if m!=method]}

@router.post('/assets/{asset_id}/verification-recommendation')
def recommendation(asset_id:str,data:Capabilities,u=Depends(current),db=Depends(database)):
    from .main import asset_access
    asset=asset_access(db,u,asset_id,True)
    return recommend(asset.origin,data)

@router.get('/assets/{asset_id}/verification-history')
def history(asset_id:str,u=Depends(current),db=Depends(database)):
    from .main import asset_access
    asset_access(db,u,asset_id,True)
    rows=db.scalars(select(Challenge).where(Challenge.asset_id==asset_id).order_by(Challenge.created.desc()).limit(50))
    return [{'id':r.id,'method':r.method,'created':r.created,'expires':r.expires,
             'state':'consumed or revoked' if r.consumed else 'expired' if r.expires<=time.time() else 'pending'} for r in rows]

@router.get('/assets/{asset_id}/challenge/{challenge_id}/file')
def download(asset_id:str,challenge_id:str,u=Depends(current),db=Depends(database)):
    from .main import asset_access
    asset_access(db,u,asset_id,True)
    c=db.get(Challenge,challenge_id)
    if not c or c.asset_id!=asset_id or c.method!='file' or c.consumed or c.expires<=time.time():
        raise HTTPException(400,'A current file challenge is required.')
    return Response(c.token,media_type='text/plain',headers={'Content-Disposition':f'attachment; filename="aegis-{c.token}.txt"','Cache-Control':'no-store'})
