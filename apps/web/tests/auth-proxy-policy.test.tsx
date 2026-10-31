import {describe,it,expect} from 'vitest';
import {authPath,previewProxyGate,aegisSessionCookie} from '../lib/auth-proxy-policy';

const preview = 'https://pen-testing-aspz5rfpn-youssefnabilnada-1001s-projects.vercel.app';
const secret = 'A'.repeat(64);

describe('auth path boundary',()=>{
 it('permits only bounded account-route segments',()=>{
  expect(authPath(['me'])).toBe('/auth/me');
  expect(authPath(['firebase','login'])).toBe('/auth/firebase/login');
  expect(authPath(['account','sign-out-all'])).toBe('/auth/account/sign-out-all');
  for(const invalid of [[],['..','admin'],['/admin'],['%2e%2e'],['a?x=1'],Array(7).fill('x'),['']])
   expect(authPath(invalid)).toBeNull();
 });
});
describe('preview secret and exact origin',()=>{
 it('fails closed in production without its own gateway, while preserving unconfigured preview behavior',()=>{
  expect(previewProxyGate({VERCEL_ENV:'production'},preview,preview,'POST')).toEqual({allowed:false,status:503});
  expect(previewProxyGate({VERCEL_ENV:'production',AEGIS_PREVIEW_AUTH_ENABLED:'true',
    AEGIS_PREVIEW_GATEWAY_KEY:secret},preview,preview,'POST')).toEqual({allowed:false,status:503});
  expect(previewProxyGate({VERCEL_ENV:'preview'},preview,preview,'POST')).toEqual({allowed:true});
 });
 it('requires a dedicated strong production gateway key and exact browser Origin',()=>{
  const enabled={VERCEL_ENV:'production',AEGIS_PRODUCTION_GATEWAY_ENABLED:'true'};
  for(const key of ['', 'short', 'x'.repeat(64)+'!']){
   expect(previewProxyGate({...enabled,AEGIS_PRODUCTION_GATEWAY_KEY:key},preview,preview,'POST'))
    .toEqual({allowed:false,status:503});
  }
  const configured={...enabled,AEGIS_PRODUCTION_GATEWAY_KEY:secret};
  expect(previewProxyGate(configured,preview,preview,'POST')).toEqual({allowed:true,secret});
  expect(previewProxyGate(configured,null,preview,'GET')).toEqual({allowed:true,secret});
  expect(previewProxyGate(configured,null,preview,'POST')).toEqual({allowed:false,status:403});
  expect(previewProxyGate(configured,'https://evil.vercel.app',preview,'POST'))
    .toEqual({allowed:false,status:403});
 });
 it('requires a strong key in a preview deployment',()=>{
  for(const bad of ['', 'short','a'.repeat(64)+'!']){
   expect(previewProxyGate({VERCEL_ENV:'preview',AEGIS_PREVIEW_AUTH_ENABLED:'true',
       AEGIS_PREVIEW_GATEWAY_KEY:bad},preview,preview,'POST'))
     .toEqual({allowed:false,status:503});
  }
  expect(previewProxyGate({VERCEL_ENV:'production',AEGIS_PREVIEW_AUTH_ENABLED:'true',
    AEGIS_PREVIEW_GATEWAY_KEY:secret},preview,preview,'POST')).toEqual({allowed:false,status:503});
 });
 it('never permits state changes from a different or absent origin',()=>{
  const env={VERCEL_ENV:'preview',AEGIS_PREVIEW_AUTH_ENABLED:'true',
    AEGIS_PREVIEW_GATEWAY_KEY:secret};
  for(const origin of [null,'null','https://other.vercel.app',
       preview+'.evil.test','http://'+preview.slice(8)]){
    expect(previewProxyGate(env,origin,preview,'POST')).toEqual({allowed:false,status:403});
  }
  expect(previewProxyGate(env,preview,preview,'POST')).toEqual({allowed:true,secret});
  expect(previewProxyGate(env,null,preview,'GET')).toEqual({allowed:true,secret});
 });
});

describe('auth cookie forwarding',()=>{
 it('forwards only a well-formed host-only AEGIS session cookie',()=>{
  const sess='a'.repeat(43);
  expect(aegisSessionCookie('vercel_auth=sensitive; aegis_session='+sess+'; other=secret'))
   .toBe('aegis_session='+sess);
  expect(aegisSessionCookie('vercel_auth=sensitive')).toBeNull();
  expect(aegisSessionCookie('aegis_session=short')).toBeNull();
  expect(aegisSessionCookie('aegis_session=bad!token')).toBeNull();
 });
});
