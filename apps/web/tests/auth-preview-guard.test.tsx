import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import Console from '../app/console/page';
import {GET as accountAccessStatus} from '../app/api/account-access-status/route';

const response=(status:number,data:unknown)=>Promise.resolve({ok:status<400,status,json:()=>Promise.resolve(data)} as Response);
afterEach(()=>{cleanup();vi.unstubAllEnvs();vi.unstubAllGlobals()});

it('shows a safe official sign-in link when the isolated preview has no gateway',async()=>{
 const fetcher=vi.fn((url:string)=>{
  if(url==='/api/account-access-status')return response(200,{preview:true,signInConfigured:false});
  if(url==='/api/auth/me')return response(503,{detail:'Protected acceptance mode.'});
  return response(401,{});
 });
 vi.stubGlobal('fetch',fetcher);
 render(<Console/>);
 expect(await screen.findByText('Preview sign-in is not configured')).toBeTruthy();
 const link=screen.getByRole('link',{name:'Open official sign-in'});
 expect(link.getAttribute('href')).toBe('https://aegis-pentest-eg.vercel.app/console');
 expect((screen.getByRole('button',{name:'Sign in'}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.queryByText(/Account sign-in is temporarily unavailable \(HTTP 503\)/)).toBeNull();
 expect(fetcher.mock.calls.every(([url])=>url!=='/api/auth/login')).toBe(true);
});

it('reports only preview gateway configuration metadata, never a secret',async()=>{
 vi.stubEnv('VERCEL_ENV','preview');
 vi.stubEnv('AEGIS_PREVIEW_AUTH_ENABLED','false');
 vi.stubEnv('AEGIS_PREVIEW_GATEWAY_KEY','S'.repeat(64));
 const response1=await accountAccessStatus();
 expect(response1.status).toBe(200);
 const info=await response1.json();
 expect(info).toEqual({preview:true,signInConfigured:false});
 expect(JSON.stringify(info)).not.toContain('S'.repeat(64));
 vi.stubEnv('AEGIS_PREVIEW_AUTH_ENABLED','true');
 const info2=await (await accountAccessStatus()).json();
 expect(info2).toEqual({preview:true,signInConfigured:true});
});
