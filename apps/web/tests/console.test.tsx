import React from 'react';
import {render,screen,waitFor,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,describe,it,expect,vi} from 'vitest';
import Console from '../app/console/page';
const response=(status:number,data:unknown)=>Promise.resolve({ok:status<400,status,json:()=>Promise.resolve(data)} as Response);
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
describe('Workspace behavior with isolated API fixtures',()=>{
 it('prefills an emailed verification link, removes the fragment, and waits for consent',async()=>{
  const token='a'.repeat(32);window.location.hash='verify='+token;
  const f=vi.fn((url:string)=>response(401,{}));vi.stubGlobal('fetch',f);render(<Console/>);
  expect(await screen.findByRole('heading',{name:'Verify your email.'})).toBeTruthy();
  expect((screen.getByLabelText('One-time token from email') as HTMLInputElement).value).toBe(token);
  expect(window.location.hash).toBe('');
  expect(f.mock.calls.some(c=>String(c[0]).includes('/auth/verify'))).toBe(false);
 });
 it('shows honest sign-in and testing access after 401',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response(401,{})));render(<Console/>);
  expect(await screen.findByRole('heading',{name:'Welcome back.'})).toBeTruthy();
  expect(screen.getByLabelText('Email address')).toBeTruthy();
  expect(screen.getByText(/Payments are disabled/)).toBeTruthy();
 });
 it('renders a useful service error instead of success',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response(503,{})));render(<Console/>);
  expect(await screen.findByRole('alert')).toBeTruthy();
  expect(screen.getByText(/Account sign-in is temporarily unavailable \(HTTP 503\)/)).toBeTruthy();
 });
 it('registers and opens verification without pretending email is verified',async()=>{
  const f=vi.fn((url:string)=>url.endsWith('/register')?response(201,{message:'Check your email for a verification token.'}):response(401,{}));vi.stubGlobal('fetch',f);render(<Console/>);
  await screen.findByRole('heading',{name:'Welcome back.'});const user=userEvent.setup();
  await user.click(screen.getByRole('button',{name:'Register'}));
  await user.type(screen.getByLabelText('Email address'),'test@example.test');
  await user.type(screen.getByLabelText(/Password ·/),'Long-password123!');
  await user.click(screen.getByRole('button',{name:'Continue →'}));
  expect(await screen.findByRole('heading',{name:'Verify your email.'})).toBeTruthy();
  expect(f.mock.calls.some(c=>c[0]==='/api/auth/register')).toBe(true);
 });
 it('blocks launching an asset until verification and explicit consent',async()=>{
  const me={id:'user',email:'test@example.test',verified:true,superadmin:false,csrf:'test-csrf',organizations:[{id:'org',name:'Fixture organization',role:'owner'}]};
  vi.stubGlobal('fetch',vi.fn((url:string)=>{
   if(url.includes('/remediation-page'))return response(200,{items:[],total:0});
   if(url.endsWith('/challenge'))return response(200,null);
   if(url.endsWith('/me'))return response(200,me);
   if(url.endsWith('/assets'))return response(200,[{id:'asset',origin:'https://fixture.test',verified:false}]);
   if(url.endsWith('/dashboard'))return response(200,{assets:1,completed:0,open_findings:0,pending_remediation:0,severity:{},trend:[],activity:[]});
   return response(200,[]);
  }));render(<Console/>);const user=userEvent.setup();
  await screen.findByRole('heading',{name:'Your security, in focus.'});
  await user.click(screen.getByRole('button',{name:'My websites'}));
  await user.click(await screen.findByRole('button',{name:'Configure'}));
  const launch=screen.getByRole('button',{name:'Launch assessment'}) as HTMLButtonElement;
  expect(launch.disabled).toBe(true);
  await user.click(screen.getByRole('checkbox',{name:/I control this asset/}));
  expect(launch.disabled).toBe(true);
 });
});

it('browses older remediation pages and resets pagination for filters',async()=>{
 const me={id:'u',email:'owner@example.test',verified:true,superadmin:false,csrf:'c',organizations:[{id:'o',name:'Workspace',role:'owner'}]};
 const fetcher=vi.fn((url:string)=>{
  if(url.endsWith('/me'))return response(200,me);
  if(url.includes('/remediation-page'))return response(200,{items:[],total:101});
  if(url.endsWith('/dashboard'))return response(200,{assets:0,completed:0,open_findings:0,pending_remediation:0,severity:{},trend:[],activity:[]});
  return response(200,[]);
 });vi.stubGlobal('fetch',fetcher);render(<Console/>);const user=userEvent.setup();
 await screen.findByRole('heading',{name:'Your security, in focus.'});
 await user.click(screen.getByRole('button',{name:'Remediation'}));
 await screen.findByText('101 matching requests');
 await user.click(screen.getByRole('button',{name:'Next requests'}));
 await waitFor(()=>expect(fetcher.mock.calls.some(([p])=>p.includes('/remediation-page?offset=25'))).toBe(true));
 await user.selectOptions(screen.getByLabelText('Remediation status'),'closed');
 await waitFor(()=>expect(fetcher.mock.calls.some(([p])=>p.includes('/remediation-page?offset=0&limit=25&status=closed'))).toBe(true));
});
it('localizes the sign-in form while keeping its authentication contract',async()=>{
 localStorage.removeItem('aegis-language');
 vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:401,headers:{'Content-Type':'application/json'}})));
 render(<Console/>);
 await screen.findByLabelText('Email address');
 await userEvent.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));
 expect(screen.getByLabelText('البريد الإلكتروني')).toBeTruthy();
 expect(screen.getByLabelText('كلمة المرور · 12 حرفًا على الأقل')).toBeTruthy();
 expect(screen.getByRole('button',{name:'تسجيل الدخول ←'})).toBeTruthy();
 expect(screen.getByLabelText('كلمة المرور · 12 حرفًا على الأقل').getAttribute('minlength')).toBe('12');
 localStorage.removeItem('aegis-language');
});


it('guides real pilot login, separates email tokens from MFA and clears stale form errors on navigation',async()=>{
 vi.stubGlobal('fetch',vi.fn((url:string)=>url.endsWith('/auth/me')?response(401,{}):response(401,{detail:'Invalid email or password.'})));
 render(<Console/>);
 await screen.findByRole('heading',{name:'Welcome back.'});
 expect(screen.getByText(/Enter the exact account email, including any \+alias/)).toBeTruthy();
 const user=userEvent.setup();
 await user.type(screen.getByLabelText('Email address'),'pilot+aegis-pilot@gmail.com');
 await user.type(screen.getByLabelText('Password · at least 12 characters'),'Fixture-only-password123!');
 await user.type(screen.getByLabelText('Authenticator or recovery code (if enabled)'),'this-is-not-a-mfa-code');
 await user.click(screen.getByRole('button',{name:'Sign in →'}));
 expect(await screen.findByText(/Check the exact AEGIS account address/)).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Verify email'}));
 expect(screen.queryByText(/Check the exact AEGIS account address/)).toBeNull();
 expect(screen.getByText(/not the old mail delivery test/)).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Sign in'}));
 expect((screen.getByLabelText('Authenticator or recovery code (if enabled)') as HTMLInputElement).value).toBe('');
 expect((screen.getByLabelText('Password · at least 12 characters') as HTMLInputElement).value).toBe('');
});
