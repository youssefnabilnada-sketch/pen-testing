import {describe,it,expect} from 'vitest';
import {authPath,previewProxyGate} from '../lib/auth-proxy-policy';

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
 it('does not add a privileged header in normal production or unconfigured preview',()=>{
  expect(previewProxyGate({VERCEL_ENV:'production'},preview,preview,'POST')).toEqual({allowed:true});
  expect(previewProxyGate({VERCEL_ENV:'preview'},preview,preview,'POST')).toEqual({allowed:true});
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
