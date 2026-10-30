// @vitest-environment node
import {afterEach,describe,expect,it,vi} from 'vitest';
import type {NextRequest} from 'next/server';
import {safeBusinessPath,businessGate} from '../lib/business-proxy-policy';
import {GET,POST} from '../app/api/[...path]/route';

const preview='https://pen-testing-3l4m8u5fi-youssefnabilnada-1001s-projects.vercel.app';
const api='https://aegis-pentest-eg-api.duckdns.org';
const key='k'.repeat(64);

const context=(path:string[])=>({params:Promise.resolve({path})});
function request(method:string,endpoint:string,headers?:Record<string,string>):NextRequest {
 const h=new Headers(headers);
 const b=new TextEncoder().encode('{"name":"example"}');
 return {
   method,
   headers:h,
   nextUrl:new URL(preview+endpoint),
   arrayBuffer:async()=>b.buffer,
 } as unknown as NextRequest;
}
afterEach(()=>{vi.unstubAllEnvs();vi.unstubAllGlobals()});

describe('private business gateway boundaries',()=>{
 it('rejects path escapes, auth bypass and long/invalid segments',()=>{
  expect(safeBusinessPath(['organizations','abc-123','dashboard'])).toBe('/organizations/abc-123/dashboard');
  for(const p of [[],['auth','login'],['..'],['a/b'],['%2F'],['http:'],['s?x=1'],Array(13).fill('ok'),['']])
    expect(safeBusinessPath(p)).toBeNull();
 });
 it('only exposes health without a secret; denies business traffic by default',()=>{
  expect(businessGate({},'/health','GET',null,preview)).toEqual({allowed:true});
  expect(businessGate({},'/organizations','GET',null,preview)).toEqual({allowed:false,status:503});
  expect(businessGate({VERCEL_ENV:'production',AEGIS_PREVIEW_AUTH_ENABLED:'true',AEGIS_PREVIEW_GATEWAY_KEY:key},
    '/organizations','GET',null,preview)).toEqual({allowed:false,status:503});
 });
 it('requires exact Origin for mutating requests',()=>{
  const env={VERCEL_ENV:'preview',AEGIS_PREVIEW_AUTH_ENABLED:'true',AEGIS_PREVIEW_GATEWAY_KEY:key};
  expect(businessGate(env,'/organizations','POST',preview,preview)).toEqual({allowed:true,secret:key});
  expect(businessGate(env,'/organizations','POST',null,preview)).toEqual({allowed:false,status:403});
  expect(businessGate(env,'/organizations','POST',preview+'.evil.test',preview)).toEqual({allowed:false,status:403});
 });
 it('forwards a report stream, disposition and only scoped account cookie',async()=>{
  vi.stubEnv('VERCEL_ENV','preview');
  vi.stubEnv('AEGIS_PREVIEW_AUTH_ENABLED','true');
  vi.stubEnv('AEGIS_PREVIEW_GATEWAY_KEY',key);
  vi.stubEnv('API_INTERNAL_URL',api);
  const spy=vi.fn(async (_url:string,init:RequestInit)=>{
   const h=new Headers(init.headers);
   expect(h.get('X-AEGIS-Preview-Gateway')).toBe(key);
   expect(h.get('X-Forwarded-For')).toBe(null);
   expect(h.get('Cookie')).toBe('aegis_session='+('a'.repeat(43)));
   return new Response(new Uint8Array([37,80,68,70]),{status:200,headers:{
    'Content-Type':'application/pdf','Content-Disposition':'attachment; filename="audit.pdf"',
    'Set-Cookie':'evil=x',
   }});
  });
  vi.stubGlobal('fetch',spy);
  const result=await GET(request('GET','/api/assessments/abc/report',{
    Cookie:'vercel_auth=private; aegis_session='+('a'.repeat(43))+'; unrelated=secret',
    'X-Forwarded-For':'127.0.0.1',
  }),context(['assessments','abc','report']));
  expect(result.status).toBe(200);
  expect(result.headers.get('Content-Disposition')).toContain('audit.pdf');
  expect(result.headers.get('Set-Cookie')).toBe(null);
  expect(spy.mock.calls[0][0]).toBe(api+'/assessments/abc/report');
 });
 it('blocks unprotected business writes and never calls upstream',async()=>{
  vi.stubEnv('API_INTERNAL_URL',api);
  vi.stubEnv('VERCEL_ENV','preview');
  const spy=vi.fn();
  vi.stubGlobal('fetch',spy);
  const res=await POST(request('POST','/api/organizations',{
   Origin:preview,'Content-Type':'application/json',
  }),context(['organizations']));
  expect(res.status).toBe(503);
  expect(spy).not.toHaveBeenCalled();
 });
 it('allows health while in protected stage',async()=>{
  vi.stubEnv('API_INTERNAL_URL',api);
  vi.stubEnv('VERCEL_ENV','preview');
  const spy=vi.fn(async()=>new Response('{"database":"reachable"}',{status:200,headers:{'Content-Type':'application/json'}}));
  vi.stubGlobal('fetch',spy);
  const res=await GET(request('GET','/api/health'),context(['health']));
  expect(res.status).toBe(200);
  expect(spy).toHaveBeenCalledOnce();
 });
});
