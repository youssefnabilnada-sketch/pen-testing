"""Reviewed, code-shipped passive detectors. No network access or executable feed input."""
from http.cookies import SimpleCookie
from .policies import csp_directives,single_csp
from .safety import Observation
CATALOG={
 'header.referrer':{'version':'1','title':'Referrer Policy not observed','fix':'Review and set an explicit Referrer-Policy appropriate to application privacy needs.','reference':'https://owasp.org/www-project-secure-headers/'},
 'csp.base-uri':{'version':'1','title':'CSP base-uri directive not observed','fix':"Review base-element usage and test an explicit base-uri 'self' or 'none' directive in staging.",'reference':'https://www.w3.org/TR/CSP3/#directive-base-uri'},
 'cookie.samesite':{'version':'1','title':'A cookie has no recognized explicit SameSite setting','fix':'Review cookie purpose and test an explicit SameSite=Lax or Strict where appropriate; cross-site cookies may need None with Secure. Browser defaults are not evidence of exploitability.','reference':'https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie'},
}
def evaluate(key,response):
    """Return (observation, not_performed_reason); both None means tested/no signal."""
    rule=CATALOG[key];reason=None;detected=False
    if key=='header.referrer':
        detected=not any(k.lower()=='referrer-policy' for k,_ in response.headers)
        evidence='Referrer-Policy was absent. Browser defaults and application context require review.'
    elif key=='csp.base-uri':
        policy=single_csp(response.headers)
        if not policy:reason='No single supported enforced CSP policy was available.'
        else:detected='base-uri' not in csp_directives(policy)
        evidence='A single enforced CSP did not contain a base-uri directive. No injection or exploitation was attempted.'
    else:
        cookies=[];unparseable=False
        for name,value in response.headers:
            if name.lower()!='set-cookie':continue
            jar=SimpleCookie()
            try:jar.load(value)
            except Exception:unparseable=True;continue
            if not jar:unparseable=True
            cookies.extend(jar.values())
        if not cookies or unparseable:reason='No complete parseable cookie evidence; prior cookie settings are not proven fixed.'
        else:detected=any(c['samesite'].lower() not in ('lax','strict','none') for c in cookies)
        evidence='At least one response cookie lacked a recognized explicit SameSite setting. Cookie names and values are omitted; browser defaults and purpose require review.'
    if reason:return None,reason
    if not detected:return None,None
    return {'rule':key,'title':rule['title'],'severity':'low','confidence':'high','evidence':evidence,'remediation':rule['fix'],'detection_method':'bounded GET / response configuration','reference':rule['reference'],'classification':'verified configuration observation; impact requires human review'},None
def fixtures(key):
    if key=='header.referrer':return [(Observation(200,[],b''),True,False),(Observation(200,[('Referrer-Policy','no-referrer')],b''),False,False)]
    if key=='csp.base-uri':return [
        (Observation(200,[('Content-Security-Policy',"default-src 'none'")],b''),True,False),
        (Observation(200,[('Content-Security-Policy',"base-uri 'none'")],b''),False,False),
        (Observation(200,[],b''),False,True),
        (Observation(200,[('Content-Security-Policy',"default-src 'none'"),('Content-Security-Policy',"base-uri 'none'")],b''),False,True)]
    return [(Observation(200,[('Set-Cookie','fixture=private; Secure; HttpOnly')],b''),True,False),
        (Observation(200,[('Set-Cookie','fixture=private; Secure; HttpOnly; SameSite=Lax')],b''),False,False),
        (Observation(200,[],b''),False,True)]
def validate(key):
    cases=fixtures(key)
    for response,expected,unverified in cases:
        observation,reason=evaluate(key,response)
        if bool(observation)!=expected or bool(reason)!=unverified:raise ValueError('Code-owned detector fixture failed.')
    return len(cases)


def evidence_valid(record):
    import json
    if not record or record.key not in CATALOG or record.version != CATALOG[record.key]['version']:
        return False
    try:
        evidence = json.loads(record.test_evidence)
    except (ValueError, TypeError):
        return False
    return isinstance(evidence, dict) and evidence.get('version') == record.version and evidence.get('result') == 'passed' and evidence.get('tests') == len(fixtures(record.key))


def active(record):
    return bool(record and record.enabled and record.approved_by and evidence_valid(record))
