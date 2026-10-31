import {AEGIS_AUTH_HOST,helperProject} from './firebase-first-party';
import type {FirebaseFeatureEnv} from './firebase-first-party';

/**
 * Proxy only Firebase's public helper resources. The browser's AEGIS session,
 * CSRF token and authorization headers MUST NOT reach Firebase Hosting.
 */
const HELPER_FILES=new Set([
 'handler','handler.js','iframe','iframe.js',
 'experiments.js','links','links.js',
]);
const INIT='/__/firebase/init.json';

export async function firebaseHelperProxy(
 request:Request, path:string, env:FirebaseFeatureEnv=process.env as unknown as FirebaseFeatureEnv,
 fetcher:typeof fetch=fetch
):Promise<Response> {
 const project=helperProject(env);
 if(!project)return new Response('Not found.',{status:404});
 if(path!==INIT && !(path.startsWith('/__/auth/') && HELPER_FILES.has(path.slice('/__/auth/'.length))))
  return new Response('Not found.',{status:404});
 if(!['GET','HEAD','POST'].includes(request.method))
  return new Response('Method not allowed.',{status:405});
 if(request.method==='POST' && path!== '/__/auth/handler')
  return new Response('Method not allowed.',{status:405});
 const input=new URL(request.url);
 if(input.search.length>16000)return new Response('Bad request.',{status:400});
 const upstreamOrigin=`https://${project}.firebaseapp.com`;
 const url=upstreamOrigin+path+input.search;
 const headers=new Headers({Accept:request.headers.get('accept')||'*/*'});
 let body:ArrayBuffer|undefined;
 if(request.method==='POST'){
  const type=request.headers.get('content-type')||'';
  if(!type.toLowerCase().startsWith('application/x-www-form-urlencoded'))
   return new Response('Unsupported content type.',{status:415});
  body=await request.arrayBuffer();
  if(body.byteLength>65536)return new Response('Request too large.',{status:413});
  headers.set('Content-Type','application/x-www-form-urlencoded');
 }
 let upstream:Response;
 try{
  upstream=await fetcher(url,{method:request.method,headers,body,redirect:'manual',cache:'no-store',signal:AbortSignal.timeout(15000)});
 }catch{
  return new Response('Auth helper temporarily unavailable.',{status:503,headers:{'Cache-Control':'no-store'}});
 }
 const responseHeaders=new Headers({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
 const type=upstream.headers.get('content-type');
 if(type)responseHeaders.set('Content-Type',type);
 // The Firebase helper iframe is first party, unlike arbitrary website embeds.
 if(path.startsWith('/__/auth/'))responseHeaders.set('X-Frame-Options','SAMEORIGIN');
 if(upstream.status>=300&&upstream.status<400){
  const location=upstream.headers.get('location');
  if(!location)return new Response('Unexpected auth redirect.',{status:502});
  let destination:URL;
  try{destination=new URL(location,url)}catch{return new Response('Unexpected auth redirect.',{status:502})}
  if(destination.origin===upstreamOrigin && destination.pathname.startsWith('/__/auth/')){
   responseHeaders.set('Location',`https://${AEGIS_AUTH_HOST}${destination.pathname}${destination.search}${destination.hash}`);
  }else if(destination.protocol==='https:' && (destination.hostname==='accounts.google.com'||destination.hostname==='accounts.youtube.com')){
   responseHeaders.set('Location',destination.toString());
  }else return new Response('Unexpected auth redirect.',{status:502});
  return new Response(null,{status:upstream.status,headers:responseHeaders});
 }
 if(upstream.status===204||request.method==='HEAD')return new Response(null,{status:upstream.status,headers:responseHeaders});
 // Never forward Set-Cookie or arbitrary headers from the public helper origin.
 return new Response(await upstream.arrayBuffer(),{status:upstream.status,headers:responseHeaders});
}
