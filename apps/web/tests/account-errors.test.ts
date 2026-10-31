import {describe,it,expect} from 'vitest';
import {accountErrorMessage,ACCOUNT_NETWORK_ERROR} from '../app/console/account-errors';

describe('account error information stays helpful without leaking internal details',()=>{
 it('separates failed credentials from temporary gateway errors',()=>{
  expect(accountErrorMessage(401,'/auth/login')).toMatch(/Invalid email or password/);
  expect(accountErrorMessage(502,'/auth/login','upstream internal secret')).toMatch(/HTTP 502/);
  expect(accountErrorMessage(503,'/auth/login','gateway internal secret')).toMatch(/HTTP 503/);
  expect(accountErrorMessage(502,'/auth/login','upstream internal secret')).not.toMatch(/internal secret/);
  expect(accountErrorMessage(503,'/auth/login')).toMatch(/not identified as incorrect/);
 });
 it('identifies throttling and policy blocks without making success claims',()=>{
  expect(accountErrorMessage(429,'/auth/login')).toMatch(/HTTP 429/);
  expect(accountErrorMessage(403,'/auth/login')).toMatch(/HTTP 403/);
  expect(accountErrorMessage(500,'/auth/login','internal stack trace')).not.toMatch(/stack trace/);
 });
 it('still displays safe validation feedback for 4xx requests',()=>{
  expect(accountErrorMessage(422,'/auth/verify','One-time token required')).toBe('One-time token required');
  expect(accountErrorMessage(400,'/auth/reset')).toMatch(/HTTP 400/);
  expect(accountErrorMessage(400,'/auth/reset','x'.repeat(241))).not.toContain('x'.repeat(100));
 });
 it('does not suggest bad passwords when networking fails',()=>{
  expect(ACCOUNT_NETWORK_ERROR).toMatch(/Could not connect/);
 });
});
