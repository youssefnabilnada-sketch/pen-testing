from typing import Literal
from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from sqlalchemy import select
from .auth import current,member,audit
from .db import database
from .models import NotificationPreference,NotificationRead,Notification,User
KINDS=['advisory_impact','finding_change','assessment_failed','schedule_blocked','remediation_retest','health_change']
router=APIRouter(tags=['Personal notification settings'])
class Preferences(BaseModel):
    enabled_kinds:list[Literal['advisory_impact','finding_change','assessment_failed','schedule_blocked','remediation_retest','health_change']]=Field(max_length=6)
def settings(db,u,org):
    p=db.get(NotificationPreference,(org,u.id))
    return p.enabled_kinds if p else KINDS
@router.get('/organizations/{org}/notification-preferences')
def get_preferences(org:str,u=Depends(current),db=Depends(database)):
    member(db,u,org)
    return {'enabled_kinds':settings(db,u,org),'channel':'in_app'}
@router.put('/organizations/{org}/notification-preferences')
def put_preferences(org:str,data:Preferences,u=Depends(current),db=Depends(database)):
    member(db,u,org)
    db.scalar(select(User).where(User.id==u.id).with_for_update())
    p=db.get(NotificationPreference,(org,u.id))
    if not p:p=NotificationPreference(org_id=org,user_id=u.id);db.add(p)
    p.enabled_kinds=sorted(set(data.enabled_kinds));audit(db,u,'notifications.preferences_changed',u.id,org);db.commit()
    return {'enabled_kinds':p.enabled_kinds,'channel':'in_app'}
def visible(db,u,org):
    read=select(NotificationRead.notification_id).where(NotificationRead.user_id==u.id)
    rows=db.execute(select(Notification,Notification.id.in_(read).label('was_read')).where(Notification.org_id==org,Notification.kind.in_(settings(db,u,org))).order_by(Notification.created.desc(),Notification.id).limit(100))
    return [{'id':n.id,'kind':n.kind,'title':n.title,'detail':n.detail,'created':n.created,'read':bool(was_read)} for n,was_read in rows]
def mark_read(db,u,n):
    member(db,u,n.org_id)
    db.scalar(select(User).where(User.id==u.id).with_for_update())
    if not db.get(NotificationRead,(n.id,u.id)):
        db.add(NotificationRead(notification_id=n.id,user_id=u.id))
    db.commit();return {'read':True}
