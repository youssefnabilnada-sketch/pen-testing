"""Deterministic response configuration observations, never exploitability claims."""
import time
from http.cookies import SimpleCookie
from .policies import csp_directives,single_csp

RULES = {
 'transport.http':('Unencrypted HTTP response','medium','Serve this endpoint over HTTPS and plan a separately scoped redirect check.'),
 'header.hsts':('HSTS header not observed','medium','After validating HTTPS coverage, deploy Strict-Transport-Security with an appropriate max-age.'),
 'header.csp':('Content Security Policy not observed','medium','Develop a restrictive CSP in report-only mode, validate it, then enforce it.'),
 'csp.inline':('CSP permits unsafe script execution signals','medium','Review unsafe-inline and unsafe-eval in script directives; prefer nonces or hashes.'),
 'header.nosniff':('MIME-sniffing protection not observed','low','Set X-Content-Type-Options: nosniff.'),
 'header.frame':('Frame embedding restriction not observed','low','Set a suitable CSP frame-ancestors directive or X-Frame-Options.'),
 'cookie.secure':('A response cookie lacks Secure','medium','Apply Secure to security-sensitive cookies after HTTPS validation.'),
 'cookie.httponly':('A response cookie lacks HttpOnly','low','Apply HttpOnly to session cookies that do not need JavaScript access. Human review must determine purpose.'),
 'tls.expiry':('TLS certificate expires within 30 days','medium','Renew the certificate and verify deployment across endpoints.'),
 'hsts.short':('HSTS max-age is missing or short','low','Review HSTS rollout and choose a suitable nonzero max-age.'),
}

def analyze(origin, response):
    headers = {k.lower():v for k,v in response.headers}
    found = {}
    def add(rule, evidence):
        title, severity, fix = RULES[rule]
        found[rule] = {'rule':rule,'title':title,'severity':severity,'confidence':'high','evidence':evidence,'remediation':fix,'detection_method':'bounded GET / response configuration','reference':'OWASP Secure Headers Project','classification':'verified observation; impact requires review'}
    if origin.startswith('http:'):add('transport.http','The explicitly authorized origin used HTTP.')
    if origin.startswith('https:'):
        if 'strict-transport-security' not in headers:add('header.hsts','Strict-Transport-Security was absent on this response.')
        else:
            import re
            age=re.search(r'(?i)(?:^|;)\s*max-age\s*=\s*(\d+)',headers['strict-transport-security'])
            if not age or int(age.group(1))<86400:add('hsts.short','HSTS max-age was absent or below one day.')
    csp = next((v.lower() for k,v in response.headers if k.lower()=='content-security-policy' and v.strip()),'')
    single=single_csp(response.headers)
    directives=csp_directives(single) if single else {}
    if not csp:add('header.csp','Content-Security-Policy was absent on this response.')
    elif single is not None:
        script=directives.get('script-src',directives.get('default-src',[]))
        if "'unsafe-inline'" in script or "'unsafe-eval'" in script:add('csp.inline','The effective script policy contains unsafe-inline or unsafe-eval; contextual review required.')
    if headers.get('x-content-type-options','').lower()!='nosniff':add('header.nosniff','X-Content-Type-Options: nosniff was not observed.')
    if (not csp or single is not None) and ('frame-ancestors' not in directives or '*' in directives['frame-ancestors']) and headers.get('x-frame-options','').lower() not in ('deny','sameorigin'):add('header.frame','Neither a non-wildcard frame-ancestors directive nor a recognized X-Frame-Options restriction was observed.')
    for key,value in response.headers:
        if key.lower()=='set-cookie':
            cookie=SimpleCookie()
            try:cookie.load(value)
            except Exception:continue
            for morsel in cookie.values():
                if not morsel['secure']:add('cookie.secure','At least one Set-Cookie header lacked Secure. Cookie names and values are intentionally omitted.')
                if not morsel['httponly']:add('cookie.httponly','At least one Set-Cookie header lacked HttpOnly. Cookie purpose requires human review.')
    if response.tls and response.tls['expires']-time.time()<30*86400:add('tls.expiry','A validated certificate expires within 30 days.')
    return list(found.values())
