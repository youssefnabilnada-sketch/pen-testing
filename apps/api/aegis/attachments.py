"""Small text-only evidence; never execute or render uploaded documents."""
import re
import base64
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from .db import database
from .auth import current,member,audit
from .models import Attachment,Remediation
from .support import ticket
router=APIRouter(prefix='/files',tags=['Evidence attachments'])
class AttachmentBodyLimit:
    def __init__(self,app):self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope.get('method')!='POST' or not scope.get('path','').startswith('/files/'):
            return await self.app(scope,receive,send)
        body=bytearray()
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            body.extend(message.get('body',b''))
            if len(body)>2*1024*1024:
                response=Response('Attachment request exceeds 2 MiB.',status_code=413)
                return await response(scope,receive,send)
            if not message.get('more_body',False):break
        consumed=False
        async def bounded_receive():
            nonlocal consumed
            if consumed:return await receive()
            consumed=True
            return {'type':'http.request','body':bytes(body),'more_body':False}
        return await self.app(scope,bounded_receive,send)
class Upload(BaseModel):
    filename:str=Field(min_length=5,max_length=100)
    content:str=Field(min_length=1,max_length=350000)
    internal:bool=False
    encoding:Literal['text','base64']='text'
def access(db,u,kind,target,write=False):
    if kind in ('support','staff-support'):
        parent=ticket(db,u,target,staff=kind=='staff-support',write=write)
        private=kind=='staff-support'
        field=Attachment.support_ticket_id
    elif kind=='remediation':
        parent=db.scalar(select(Remediation).where(Remediation.id==target).with_for_update())
        if not parent:raise HTTPException(404,'Record not found.')
        membership=member(db,u,parent.org_id,write=write)
        private=membership.role in ('owner','admin','engineer')
        field=Attachment.remediation_id
    else:raise HTTPException(404,'Unsupported attachment location.')
    return parent,private,field
def record(a):
    return {'id':a.id,'filename':a.filename,'size':a.size,'internal':a.internal,'created':a.created}
@router.get('/{kind}/{target}')
def listing(kind:str,target:str,u=Depends(current),db=Depends(database)):
    _,private,field=access(db,u,kind,target)
    q=select(Attachment.id,Attachment.filename,Attachment.size,Attachment.internal,Attachment.created).where(field==target)
    if not private:q=q.where(Attachment.internal.is_(False))
    return [record(a) for a in db.execute(q.order_by(Attachment.created,Attachment.id).limit(20))]
@router.post('/{kind}/{target}',status_code=201)
def upload(kind:str,target:str,data:Upload,u=Depends(current),db=Depends(database)):
    from .main import throttle
    parent,private,field=access(db,u,kind,target,True);throttle('attachments:'+u.id)
    if parent.status in ('closed','rejected'):raise HTTPException(409,'Record is closed.')
    if data.internal and not private:raise HTTPException(403,'Internal attachment permission required.')
    if data.encoding=='base64':
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _.-]{0,94}\.png',data.filename) or '..' in data.filename:raise HTTPException(422,'PNG filename required.')
        try:
            from .image_evidence import sanitize_png
            data.content,size=sanitize_png(data.content)
        except Exception:raise HTTPException(422,'Invalid PNG or image limits exceeded.')
    else:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _.-]{0,94}\.(txt|log|csv|md)',data.filename) or '..' in data.filename:
            raise HTTPException(422,'Use a simple .txt, .log, .csv or .md filename.')
        try:size=len(data.content.encode('utf-8'))
        except UnicodeError:raise HTTPException(422,'Invalid UTF-8 text.')
        if size>262144:raise HTTPException(413,'Text attachment exceeds 256 KiB.')
        if any(ord(c)<32 and c not in '\n\r\t' for c in data.content):raise HTTPException(422,'Binary/control content is not accepted.')
    if db.scalar(select(func.count()).select_from(Attachment).where(field==target))>=20:
        raise HTTPException(409,'Maximum 20 attachments per record. Remove an old file first.')
    a=Attachment(user_id=u.id,filename=data.filename,content=data.content,size=size,internal=data.internal)
    setattr(a,field.key,target);db.add(a);db.flush();audit(db,u,'attachment.uploaded',a.id,parent.org_id);db.commit()
    return record(a)
def locate(db,u,kind,target,aid,write=False):
    parent,private,field=access(db,u,kind,target,write)
    a=db.scalar(select(Attachment).where(Attachment.id==aid,field==target))
    if not a or (a.internal and not private):raise HTTPException(404,'Attachment not found.')
    return parent,a
@router.get('/{kind}/{target}/{aid}')
def download(kind:str,target:str,aid:str,u=Depends(current),db=Depends(database)):
    parent,a=locate(db,u,kind,target,aid)
    audit(db,u,'attachment.downloaded',a.id,parent.org_id);db.commit()
    return Response(base64.b64decode(a.content) if a.filename.endswith('.png') else a.content.encode('utf-8'),media_type='application/octet-stream',headers={'Content-Disposition':f'attachment; filename="{a.filename}"','X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})
@router.delete('/{kind}/{target}/{aid}')
def remove(kind:str,target:str,aid:str,u=Depends(current),db=Depends(database)):
    parent,a=locate(db,u,kind,target,aid,True)
    if kind!='staff-support' and a.user_id!=u.id:
        member(db,u,parent.org_id,roles=['owner','admin'])
    aid=a.id;db.delete(a);audit(db,u,'attachment.deleted',aid,parent.org_id);db.commit()
    return {'message':'Attachment deleted.'}
