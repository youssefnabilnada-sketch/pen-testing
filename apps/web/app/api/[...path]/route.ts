import type {NextRequest} from 'next/server';
import {apiOrigin} from '../../../lib/deployment';
import {businessGate,safeBusinessPath} from '../../../lib/business-proxy-policy';
import {aegisSessionCookie} from '../../../lib/auth-proxy-policy';

export const runtime='nodejs';
export const dynamic='force-dynamic';
type Context={params:Promise<{path:string[]}>};

async function proxyBusiness(request:NextRequest, context:Context):Promise<Response>{
  const path=safeBusinessPath((await context.params).path);
  if(!path)return new Response('Not found.',{status:404});
  const gate=businessGate(process.env,path,request.method,request.headers.get('origin'),request.nextUrl.origin);
  if(!gate.allowed)return new Response('Protected acceptance mode.',{status:gate.status});

  if(request.nextUrl.search.length>2048)return new Response('Query too large.',{status:414});
  const headers=new Headers({Accept:request.headers.get('accept')||'application/json'});
  const cookie=aegisSessionCookie(request.headers.get('cookie'));
  if(cookie)headers.set('Cookie',cookie);
  for(const key of ['origin','x-csrf-token']){
    const value=request.headers.get(key);
    if(value)headers.set(key,value);
  }
  if(gate.secret)headers.set('X-AEGIS-Preview-Gateway',gate.secret);
  let body: string|undefined;
  if(!['GET','HEAD'].includes(request.method)){
    const type=request.headers.get('content-type')?.split(';',1)[0]?.trim().toLowerCase();
    if(type!=='application/json')return new Response('JSON content required.',{status:415});
    const length=Number(request.headers.get('content-length')||0);
    if(!Number.isSafeInteger(length)||length<0||length>2097152)
      return new Response('Request too large.',{status:413});
    const data=await request.arrayBuffer();
    if(data.byteLength>2097152)return new Response('Request too large.',{status:413});
    body=new TextDecoder().decode(data);
    headers.set('Content-Type','application/json');
  }
  let upstream:Response;
  try{
    upstream=await fetch(apiOrigin(process.env)+path+request.nextUrl.search,{
      method:request.method,
      headers,
      body,
      redirect:'manual',
      cache:'no-store',
      signal:AbortSignal.timeout(30000),
    });
  }catch{
    return new Response('Backend temporarily unavailable.',{
      status:503,headers:{'Cache-Control':'no-store'},
    });
  }
  if(upstream.status>=300&&upstream.status<400)
    return new Response('Unexpected upstream redirect.',{status:502});
  const outgoing=new Headers({
    'Cache-Control':'no-store',
    'X-Content-Type-Options':'nosniff',
    'X-Frame-Options':'DENY',
  });
  const type=upstream.headers.get('content-type');
  if(type)outgoing.set('Content-Type',type);
  const disposition=upstream.headers.get('content-disposition');
  if(disposition && !/[\r\n]/.test(disposition) && disposition.length<300)
    outgoing.set('Content-Disposition',disposition);
  // Business routes never issue session cookies; only /api/auth/* is allowed
  // to set/delete the first-party aegis_session cookie.
  return new Response(request.method==='HEAD'||upstream.status===204?null:upstream.body,{
    status:upstream.status,
    headers:outgoing,
  });
}

export const GET=proxyBusiness;
export const POST=proxyBusiness;
export const PUT=proxyBusiness;
export const PATCH=proxyBusiness;
export const DELETE=proxyBusiness;
export const HEAD=proxyBusiness;
