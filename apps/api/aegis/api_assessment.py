"""Non-destructive API response checks; no authentication bypass or payload injection."""
import time
RULES={
 'api.transport':('API endpoint uses HTTP','medium','Serve the approved endpoint over HTTPS.'),
 'api.nosniff':('API MIME-sniffing protection not observed','low','Set X-Content-Type-Options: nosniff for API responses.'),
 'api.content_type':('JSON media type not observed','low','Confirm the endpoint purpose and return an appropriate JSON Content-Type.'),
 'api.cors_credentials':('Wildcard CORS origin with credentials','low','Use an explicit allowlist when browser credentials are intended; browsers reject wildcard credentialed CORS.'),
 'api.tls_expiry':('API TLS certificate expires within 30 days','medium','Renew the certificate and validate all approved endpoints.'),
}
def profile(origin,response):
    headers={k.lower():v for k,v in response.headers};found=[];executed=set(RULES);missing={}
    def add(rule,evidence):
        title,severity,fix=RULES[rule]
        found.append({'rule':rule,'title':title,'severity':severity,'confidence':'high','evidence':evidence,'remediation':fix,'detection_method':'authorized API GET response headers','reference':'HTTP response configuration','classification':'verified observation; impact requires review'})
    if origin.startswith('http:'):add('api.transport','The approved API origin uses unencrypted HTTP.')
    if headers.get('x-content-type-options','').lower()!='nosniff':add('api.nosniff','X-Content-Type-Options: nosniff absent.')
    media=headers.get('content-type','').split(';')[0].strip().lower()
    if media!='application/json' and not (media.startswith('application/') and media.endswith('+json')):add('api.content_type','The response does not declare a JSON media type. Response body was not inspected.')
    if headers.get('access-control-allow-origin','').strip()=='*' and headers.get('access-control-allow-credentials','').strip().lower()=='true':add('api.cors_credentials','Wildcard origin and credential allowance appear together; this does not prove a cross-origin data leak.')
    if response.tls and isinstance(response.tls.get('expires'),(int,float)):
        if response.tls['expires']<=time.time()+30*86400:add('api.tls_expiry','Validated certificate expiry is within 30 days.')
    else:executed.remove('api.tls_expiry');missing['api.tls_expiry']='No validated certificate evidence.'
    missing.update({'authorization_logic':'No credentials or bypass tests.','injection':'No payload injection or mutation.','rate_limit':'No load or repeated rate-limit probes.','data_exposure':'Response bodies are not retained or analyzed.'})
    return found,{'version':'api-response-v1','executed':sorted(executed),'not_performed':missing,'rule_versions':{r:'1' for r in executed}}
