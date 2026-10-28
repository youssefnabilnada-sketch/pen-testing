"""UTC consent-window arithmetic; no network activity or implicit consent renewal."""
import math
def next_allowed(scope,now):
    window=scope.get('daily_window_utc',[0,24])
    if not isinstance(window,list) or len(window)!=2:raise ValueError('Invalid authorized daily window.')
    start,end=window
    if type(start) is not int or type(end) is not int or not 0<=start<end<=24:
        raise ValueError('Invalid authorized daily window.')
    begins=scope.get('window_start',0)
    if not isinstance(begins,(int,float)) or not math.isfinite(begins):raise ValueError('Invalid authorization start.')
    instant=max(now,begins)
    if start==0 and end==24:return instant
    day=math.floor(instant/86400)*86400
    opening=day+start*3600;closing=day+end*3600
    if instant<opening:return opening
    if instant+10>closing:return opening+86400
    return instant
def require_window(auth,now):
    try:
        if not isinstance(auth.scope,dict):raise ValueError('Invalid scope.')
        allowed=next_allowed(auth.scope,now)
    except (TypeError,ValueError):raise ValueError('Invalid authorized daily window.')
    if allowed>now or auth.expires-now<10:
        raise ValueError('Outside the authorized assessment window or insufficient time remains.')
