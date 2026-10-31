// @vitest-environment node
import {describe,it,expect,vi} from 'vitest';
import {firstPartyFirebaseConfig,helperProject,AEGIS_AUTH_HOST} from '../lib/firebase-first-party';
import {firebaseHelperProxy} from '../lib/firebase-helper-proxy';

const enabled={
 NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY:'true',
 NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID:'test-aegis-project',
} as NodeJS.ProcessEnv;
const disabled={} as NodeJS.ProcessEnv;
const request=(pathname:string,init?:RequestInit)=>new Request('https://aegis-pentest-eg.vercel.app'+pathname,init);

describe('feature-gated first-party OAuth helpers',()=>{
 it('stays disabled until both explicit deployment settings are provided',()=>{
  expect(helperProject(disabled)).toBeNull();
  expect(helperProject({...enabled,NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID:'evil.com'})).toBeNull();
  expect(firstPartyFirebaseConfig({projectId:'test-aegis-project',authDomain:'test-aegis-project.firebaseapp.com'},AEGIS_AUTH_HOST,disabled).authDomain).toContain('.firebaseapp.com');
 });
 it('selects same-domain helper only for exact AEGIS production hostname and verified Firebase project',()=>{
  const config={projectId:'test-aegis-project',authDomain:'test-aegis-project.firebaseapp.com'};
  expect(firstPartyFirebaseConfig(config,AEGIS_AUTH_HOST,enabled).authDomain).toBe(AEGIS_AUTH_HOST);
  expect(firstPartyFirebaseConfig(config,'other.vercel.app',enabled)).toEqual(config);
  expect(firstPartyFirebaseConfig({...config,projectId:'other-project'},AEGIS_AUTH_HOST,enabled).authDomain).toBe(config.authDomain);
 });
 it('never forwards AEGIS session cookies, bearer tokens, or CSRF to Firebase Hosting',async()=>{
  const spy=vi.fn(async (_url:string,_opts:RequestInit)=>new Response('<html>helper</html>',{status:200,headers:{'Content-Type':'text/html','Set-Cookie':'firebase-test=secret'}}));
  const result=await firebaseHelperProxy(request('/__/auth/iframe',{headers:{Cookie:'aegis_session=SECRET',Authorization:'Bearer SECRET','X-CSRF-Token':'SECRET'}}),'/__/auth/iframe',enabled,spy as typeof fetch);
  expect(result.status).toBe(200);
  expect(result.headers.get('Set-Cookie')).toBeNull();
  const headers=new Headers(spy.mock.calls[0][1].headers);
  expect(headers.has('Cookie')).toBe(false);
  expect(headers.has('Authorization')).toBe(false);
  expect(headers.has('X-CSRF-Token')).toBe(false);
  expect(result.headers.get('X-Frame-Options')).toBe('SAMEORIGIN');
 });
 it('rejects unapproved helper routes and does not become a general-purpose proxy',async()=>{
  const spy=vi.fn();
  expect((await firebaseHelperProxy(request('/__/auth/handler'),'/__/auth/handler',disabled,spy)).status).toBe(404);
  expect((await firebaseHelperProxy(request('/__/auth/other'),'/__/auth/other',enabled,spy)).status).toBe(404);
  expect((await firebaseHelperProxy(request('/__/auth/handler',{method:'DELETE'}),'/__/auth/handler',enabled,spy)).status).toBe(405);
  expect(spy).not.toHaveBeenCalled();
 });
 it('allows Google redirects, blocks arbitrary upstream redirects and rewrites Firebase helper redirects to first-party',async()=>{
  const google=vi.fn(async()=>new Response(null,{status:302,headers:{Location:'https://accounts.google.com/o/oauth2/auth?state=fixture'}}));
  const pass=await firebaseHelperProxy(request('/__/auth/handler'),'/__/auth/handler',enabled,google as typeof fetch);
  expect(pass.headers.get('location')).toContain('accounts.google.com');
  const bad=vi.fn(async()=>new Response(null,{status:302,headers:{Location:'https://evil.example/steal'}}));
  expect((await firebaseHelperProxy(request('/__/auth/handler'),'/__/auth/handler',enabled,bad as typeof fetch)).status).toBe(502);
  const old=vi.fn(async()=>new Response(null,{status:302,headers:{Location:'https://test-aegis-project.firebaseapp.com/__/auth/handler?foo=bar'}}));
  const mapped=await firebaseHelperProxy(request('/__/auth/handler'),'/__/auth/handler',enabled,old as typeof fetch);
  expect(mapped.headers.get('location')).toBe('https://aegis-pentest-eg.vercel.app/__/auth/handler?foo=bar');
 });
});
