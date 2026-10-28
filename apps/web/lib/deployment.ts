export function apiOrigin(env:NodeJS.ProcessEnv):string {
 const raw=env.API_INTERNAL_URL;
 if(env.VERCEL==='1'&&!raw)throw new Error('Set API_INTERNAL_URL to the deployed HTTPS AEGIS API before deploying the web app.');
 const url=new URL(raw||'http://localhost:8000');
 if(url.username||url.password||url.search||url.hash||url.pathname!=='/')throw new Error('API_INTERNAL_URL must be an origin without credentials, path, query or fragment.');
 if(env.VERCEL==='1'&&(url.protocol!=='https:'||['localhost','127.0.0.1','[::1]'].includes(url.hostname)))throw new Error('Vercel requires an online HTTPS API origin.');
 if(!['http:','https:'].includes(url.protocol))throw new Error('API origin must use HTTP(S).');
 return url.origin;
}
