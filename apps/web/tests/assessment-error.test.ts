import {it,expect,describe} from 'vitest';
import {assessmentFailureText} from '../lib/assessment-error';

const en=(english:string,_arabic:string)=>english;
const ar=(_english:string,arabic:string)=>arabic;
describe('public assessment failure explanations',()=>{
 it('replaces old ValueError-only failure with an honest unknown-cause explanation',()=>{
  const error='Assessment failed: ValueError. No clean result is implied.';
  expect(assessmentFailureText(error,en)).toContain('earlier job may not have recorded');
  expect(assessmentFailureText(error,ar)).toContain('لم يسجّل');
  expect(assessmentFailureText(error,en)).not.toContain('ValueError');
 });
 it('shows safe English and Arabic next steps for redirects',()=>{
  const text='The website redirected the assessment request. For safety, AEGIS does not automatically follow redirects.';
  expect(assessmentFailureText(text,en)).toContain('Verify the final website address');
  expect(assessmentFailureText(text,ar)).toContain('لا تتبع التحويلات');
 });
 it('keeps HTTP status information and never claims a scan succeeded',()=>{
  const status='The website returned HTTP 403 (access restricted).';
  expect(assessmentFailureText(status,en)).toContain('HTTP 403');
  expect(assessmentFailureText(status,ar)).toContain('HTTP 403');
  expect(assessmentFailureText(status,ar)).toContain('لم تنتج');
  expect(assessmentFailureText('The website returned HTTP 500 (server error).',ar)).toContain('HTTP 500');
 });
 it('does not display arbitrary unrecognized worker exception strings',()=>{
  expect(assessmentFailureText('secret-internal-data',en)).not.toContain('secret');
  expect(assessmentFailureText('',en)).toContain('did not finish');
 });
});
