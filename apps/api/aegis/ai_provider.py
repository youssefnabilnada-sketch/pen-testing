"""Optional bounded model advice. Model output never changes evidence or authorization."""
import http.client
import json
import os
import re
import socket
import ssl
import threading
from typing import Protocol
from urllib.parse import urlsplit
from .safety import canonical_origin,resolve
from .analyst import RULES,RuleBasedAnalyst

class EffortProvider(Protocol):
    def estimate(self,rules:list[str])->dict: ...


def configuration():
    endpoint=os.getenv('AI_CHAT_ENDPOINT','')
    p=urlsplit(endpoint)
    origin=canonical_origin('https://'+(p.netloc or ''))
    if p.scheme!='https' or p.query or p.fragment or not re.fullmatch(r'/[A-Za-z0-9/_-]*chat/completions',p.path):
        raise ValueError('Unsupported provider endpoint.')
    model=os.getenv('AI_MODEL','');key=os.getenv('AI_API_KEY','')
    if not model or len(model)>120 or not key or len(key)>4096 or any(ord(c)<32 for c in model+key):raise ValueError('Provider configuration missing or invalid.')
    return origin,p.path,model,key


def provider_state():
    if os.getenv('AI_PROVIDER_ENABLED')!='true':return {'status':'disabled','mode':'rule-based fallback','live_verified':False}
    try:configuration()
    except Exception:return {'status':'configuration_required','mode':'rule-based fallback','live_verified':False}
    return {'status':'configured','mode':'optional model-assisted effort; deterministic explanations','live_verified':False}


def provider_slot():
    if os.getenv('TESTING')=='1':return
    import redis
    with redis.Redis.from_url(os.getenv('REDIS_URL','redis://localhost:6379/0'),socket_connect_timeout=2,socket_timeout=2) as client:
        if not client.set('aegis:ai:provider-cooldown','1',nx=True,ex=30):raise ValueError('Provider cooldown active.')


def post_json(origin,path,key,payload):
    host,port,ip,scheme=resolve(origin)
    if scheme!='https':raise ValueError('HTTPS required.')
    conn=http.client.HTTPConnection(host,port,timeout=5)
    sock=socket.create_connection((ip,port),timeout=5)
    def abort():
        try:sock.shutdown(socket.SHUT_RDWR)
        except OSError:pass
    timer=threading.Timer(10,abort);timer.daemon=True;timer.start()
    try:
        sock=ssl.create_default_context().wrap_socket(sock,server_hostname=host);conn.sock=sock
        conn.request('POST',path,body=json.dumps(payload).encode(),headers={'Host':host,'Content-Type':'application/json','Authorization':'Bearer '+key,'Accept-Encoding':'identity','Connection':'close'})
        result=conn.getresponse()
        if result.status!=200:raise ValueError('Provider unavailable.')
        raw=result.read(32769)
        if len(raw)>32768:raise ValueError('Provider response too large.')
        return json.loads(raw)
    finally:
        timer.cancel();conn.close();sock.close()


def validate_advice(value,rules):
    if not isinstance(value,dict) or set(value)!={'effort'} or not isinstance(value['effort'],dict) or set(value['effort'])!=set(rules):raise ValueError('Unsupported model output.')
    if any(v not in ('small','moderate','complex','human_review') for v in value['effort'].values()):raise ValueError('Unsupported effort class.')
    return value['effort']

class ChatCompletionsProvider:
    def estimate(self,rules):
        origin,path,model,key=configuration()
        payload={'model':model,'max_tokens':800,'response_format':{'type':'json_object'},'messages':[
            {'role':'system','content':'Return JSON only: {"effort":{"rule_id":"small|moderate|complex|human_review"}}. Include exactly the supplied rule IDs. Estimate preliminary configuration remediation complexity. No vulnerability claims, prose, commands or extra fields. When application context is missing use human_review.'},
            {'role':'user','content':json.dumps([{'rule':r,'observation':RULES[r][0],'recommendation':RULES[r][2]} for r in rules])}]}
        provider_slot()
        result=post_json(origin,path,key,payload)
        choice=result['choices'][0]
        if choice.get('finish_reason')!='stop' or choice['message'].get('refusal') or choice['message'].get('tool_calls'):raise ValueError('Incomplete or refused response.')
        return validate_advice(json.loads(choice['message']['content']),rules)


def explain_with_provider(rule_ids,provider=None):
    result=RuleBasedAnalyst().explain(rule_ids)
    rules=list(dict.fromkeys(r for r in rule_ids if r in RULES))[:30]
    result['effort']={r:'human_review' for r in rules}
    result['effort_classification']='Preliminary inference; engineer review and staging validation required. Not a quotation or verified fix.'
    result['provider_status']='disabled'
    if not rules or (provider is None and os.getenv('AI_PROVIDER_ENABLED')!='true'):return result
    try:
        effort=(provider or ChatCompletionsProvider()).estimate(rules)
        result['effort']=validate_advice({'effort':effort},rules)
        result['provider_status']='responded';result['mode']='rule-based explanations with model-assisted preliminary effort'
    except Exception:
        result['provider_status']='unavailable_or_invalid';result['fallback_reason']='Model advice unavailable or rejected; deterministic guidance remains available.'
    return result
