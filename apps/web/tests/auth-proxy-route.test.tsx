// @vitest-environment node
import {describe,it,expect,vi,afterEach} from 'vitest';
import type {NextRequest} from 'next/server';
import {GET,POST} from '../app/api/auth/[...path]/route';

const preview='https://pen-testing-aspz5rfpn-youssefnabilnada-1001s-projects.vercel.app';
const backend='https://aegis-pentest-eg-api.duckdns.org';
const secret='S'.repeat(64);

function request(method:string,path:string,origin?:string,extra?:Record<string,string>):NextRequest{
 const headers=new Headers(extra);
 if(origin)headers.set('Origin',origin);
 if(method==='POST')headers.set('Content-Type','application/json');
 const body=new TextEncoder().encode('{"email":"fixture@example.test","password":"fixture"}');
 return {
   method,
   nextUrl:new URL(preview+'/api/'+path),
   headers,
   arrayBuffer:async()=>body.buffer,
 } as unknown as NextRequest;
}
const context=(segments:string[])=>({params:Promise.resolve({path:segments})});
afterEach(()=>{vi.unstubAllEnvs();vi.unstubAllGlobals()});

describe('server-only Vercel auth proxy',()=>{
 it('never reveals or forwards a supplied browser gateway header',async()=>{
  vi.stubEnv('API_INTERNAL_URL',backend);
  vi.stubEnv('AEGIS_PREVIEW_AUTH_ENABLED','false');
  vi.stubEnv('VERCEL_ENV','production');
  const stub=vi.fn(async (_url:string, options:RequestInit)=>{
   const h=new Headers(options.headers);
   expect(h.has('X-AEGIS-Preview-Gateway')).toBe(false);
   expect(h.has('X-Forwarded-For')).toBe(false);
   return new Response('{"csrf":"generated"}',{status:200,headers:{
     'Set-Cookie':'aegis_session=fixture; HttpOnly; Secure; SameSite=Strict; Path=/',
     'Content-Type':'application/json',
   }});
  });
  vi.stubGlobal('fetch',stub);
  const result=await POST(request('POST','auth/login',preview,{
    'X-AEGIS-Preview-Gateway':'attacker-controlled',
    'X-Forwarded-For':'127.0.0.1',
  }),context(['login']));
  expect(result.status).toBe(200);
  expect(result.headers.get('set-cookie')).toContain('HttpOnly; Secure; SameSite=Strict');
  expect(result.headers.get('Cache-Control')).toBe('no-store');
  expect(stub).toHaveBeenCalledOnce();
  expect(stub.mock.calls[0][0]).toBe(backend+'/auth/login');
 });
 it('staging requires a server secret and exact browser Origin before proxying writes',async()=>{
  vi.stubEnv('API_INTERNAL_URL',backend);
  vi.stubEnv('VERCEL_ENV','preview');
  vi.stubEnv('AEGIS_PREVIEW_AUTH_ENABLED','true');
  const upstream=vi.fn(async (_url:string,_options:RequestInit)=>new Response('{}',{status:422}));
  vi.stubGlobal('fetch',upstream);
  expect((await POST(request('POST','auth/login',preview),context(['login']))).status).toBe(503);
  vi.stubEnv('AEGIS_PREVIEW_GATEWAY_KEY',secret);
  expect((await POST(request('POST','auth/login','https://malicious.vercel.app'),context(['login']))).status).toBe(403);
  const result=await POST(request('POST','auth/login',preview),context(['login']));
  expect(result.status).toBe(422);
  expect(upstream).toHaveBeenCalledOnce();
  const sent=new Headers(upstream.mock.calls[0][1]?.headers);
  expect(sent.get('X-AEGIS-Preview-Gateway')).toBe(secret);
 });
 it('reads never get arbitrary browser proxy headers and invalid auth paths fail closed',async()=>{
  vi.stubEnv('API_INTERNAL_URL',backend);
  vi.stubEnv('VERCEL_ENV','preview');
  const upstream=vi.fn(async (_url:string,_options:RequestInit)=>new Response('{"enabled":true}',{status:200,headers:{'Content-Type':'application/json'}}));
  vi.stubGlobal('fetch',upstream);
  const r=await GET(request('GET','auth/firebase/config',undefined,{'X-Forwarded-For':'1.2.3.4'}),context(['firebase','config']));
  expect(r.status).toBe(200);
  expect(new Headers(upstream.mock.calls[0][1]?.headers).has('X-Forwarded-For')).toBe(false);
  expect((await GET(request('GET','auth/firebase/../../admin'),context(['..','admin']))).status).toBe(404);
 });
});
