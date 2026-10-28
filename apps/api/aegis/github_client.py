"""Fixed-host GitHub App user authentication. No repository code is executed."""
import http.client
import json
import os
import ssl
from urllib.parse import urlencode
from cryptography.fernet import Fernet

class GitHubError(ValueError):pass

def configuration():
    keys=['GITHUB_CLIENT_ID','GITHUB_CLIENT_SECRET','GITHUB_REDIRECT_URI','GITHUB_TOKEN_KEY']
    if os.getenv('GITHUB_ENABLED')!='true' or any(not os.getenv(k) for k in keys):
        raise GitHubError('GitHub connection is not configured.')
    uri=os.environ['GITHUB_REDIRECT_URI']
    if not uri.startswith('https://') or '?' in uri or '#' in uri:raise GitHubError('GitHub requires an HTTPS callback without query parameters.')
    Fernet(os.environ['GITHUB_TOKEN_KEY'].encode())
    return {k:os.environ[k] for k in keys}

def cipher():return Fernet(configuration()['GITHUB_TOKEN_KEY'].encode())

def request(host,path,method='GET',token=None,body=None):
    if host not in ('api.github.com','github.com') or not path.startswith('/') or any(ord(c)<32 for c in path):raise GitHubError('Unsupported GitHub destination.')
    conn=http.client.HTTPSConnection(host,timeout=8,context=ssl.create_default_context())
    headers={'Accept':'application/json' if host=='github.com' else 'application/vnd.github+json','User-Agent':'AEGIS-Security-Cloud','X-GitHub-Api-Version':'2022-11-28'}
    if token:headers['Authorization']='Bearer '+token
    if body is not None:headers['Content-Type']='application/json'
    try:
        conn.request(method,path,body=json.dumps(body) if body is not None else None,headers=headers)
        response=conn.getresponse();raw=response.read(1048577)
        if response.status not in (200,201,204) or len(raw)>1048576:raise GitHubError('GitHub request failed or exceeded the response limit.')
        result=json.loads(raw) if raw else {}
        if not isinstance(result,(dict,list)):raise GitHubError('Invalid GitHub response.')
        return result
    except (OSError,ValueError,http.client.HTTPException) as exc:raise GitHubError('GitHub unavailable or response rejected.') from exc
    finally:conn.close()

def authorization_url(state):
    cfg=configuration()
    return 'https://github.com/login/oauth/authorize?'+urlencode({'client_id':cfg['GITHUB_CLIENT_ID'],'redirect_uri':cfg['GITHUB_REDIRECT_URI'],'state':state})

def exchange(code):
    cfg=configuration()
    result=request('github.com','/login/oauth/access_token','POST',body={'client_id':cfg['GITHUB_CLIENT_ID'],'client_secret':cfg['GITHUB_CLIENT_SECRET'],'code':code,'redirect_uri':cfg['GITHUB_REDIRECT_URI']})
    token=result.get('access_token')
    if not isinstance(token,str) or not 1<=len(token)<=8192:raise GitHubError('GitHub authorization failed.')
    # Deliberately do not retain refresh tokens: reconnect after expiry.
    expires=min(int(result.get('expires_in',28800)),28800)
    if expires<=0:raise GitHubError('GitHub authorization expired.')
    identity=request('api.github.com','/user',token=token)
    if not isinstance(identity.get('id'),int):raise GitHubError('GitHub identity missing.')
    return token,expires,identity
