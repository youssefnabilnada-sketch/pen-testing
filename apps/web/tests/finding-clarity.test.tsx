import React from 'react';
import {cleanup,render,screen,waitFor,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,expect,it,vi} from 'vitest';
import FindingsPanel from '../app/console/FindingsPanel';
import FastFixGuidance from '../app/console/FastFixGuidance';
import IntelligencePanel from '../app/console/IntelligencePanel';
afterEach(cleanup);

const finding={id:'finding-1',title:'Missing X-Content-Type-Options',rule:'header.nosniff',origin:'https://authorized.example',severity:'low',confidence:'high',status:'open',evidence:'Observed header missing',remediation:'Add nosniff at the serving edge or app'};
it('shows a guided findings workflow and hides engineering details until requested',async()=>{
 const api=vi.fn(async(path:string)=>path.includes('finding-page')?{total:1,items:[finding]}:{total:0,items:[]});
 const open=vi.fn();
 render(<FindingsPanel api={api} org="o" role="viewer" onRemediation={async()=>{}} onOpenRemediation={open}/>);
 expect(await screen.findByText('Missing X-Content-Type-Options')).toBeTruthy();
 expect(screen.getByText(/From evidence to a verified improvement/)).toBeTruthy();
 expect(screen.getByText('Add nosniff at the serving edge or app')).toBeTruthy();
 const details=screen.getByText('Evidence and technical context').closest('details');
 expect(details?.open).toBe(false);
 expect(screen.queryByRole('button',{name:'Request remediation'})).toBeNull();
 await userEvent.click(screen.getByRole('button',{name:/My fix requests/}));
 expect(open).toHaveBeenCalledOnce();
});
it('makes lack of source access and lack of a verified fix explicit',async()=>{
 const api=vi.fn(async()=>({
  mode:'deterministic reviewed guidance',root_cause:'Owner configuration not inspected',
  recommended_action:'Test a reviewed host header rule',platform_guidance:'Use staging',
  approval:'Separate approval required',compatibility_risks:[],validation_required:[],backup_scope:'No backup created',
  capabilities:{guidance:true,reads_customer_source:false,generates_patch:false,deploys:false},
  optional_supported_adapter:{name:'github_vercel_nosniff',availability:'Separate consent required',limitations:'Only reviewed vercel.json header proposal'},
 }));
 render(<FastFixGuidance api={api} findingId="f"/>);
 const user=userEvent.setup();
 expect(api).not.toHaveBeenCalled();
 await user.click(screen.getByRole('button',{name:/Choose a remediation path/}));
 expect(await screen.findByText('No source access through this guidance')).toBeTruthy();
 expect(screen.getByText('No · approval and an implementation path required')).toBeTruthy();
 expect(screen.getByText('No · separately authorized retest required')).toBeTruthy();
 expect(screen.getByText(/limited optional adapter/)).toBeTruthy();
 expect(screen.getByText(/No fix has been applied or verified/)).toBeTruthy();
 expect(api).toHaveBeenCalledWith('/findings/f/fastfix?platform=unknown');
});
it('distinguishes scheduled 6 hour sync from last successful advisory refresh',async()=>{
 const now=Math.floor(Date.now()/1000);
 const sources=[
  {key:'cisa',interval_hours:6,enabled:true,last_success:null,last_attempt:null,next_due:now-10,error:null,coverage:'CISA catalog'},
  {key:'nvd',interval_hours:6,enabled:true,last_success:now-30,last_attempt:now-30,next_due:now+20000,error:null,coverage:'NVD'},
  {key:'github',interval_hours:6,enabled:true,last_success:now-50000,last_attempt:now-50000,next_due:now-5,error:'Queue dispatch failed',coverage:'GHSA'},
 ];
 const api=vi.fn(async(path:string)=>path==='/intelligence/sources'?sources:path.includes('/organizations/')?{inventory:[],impacts:[],notifications:[],schedules:[],retests:[]}:path.endsWith('/rules')?{built_in:[],candidates:[]}:[]);
 render(<IntelligencePanel api={api} org="org" assets={[]} isAdmin={false}/>);
 expect(await screen.findByText('Not yet synchronized')).toBeTruthy();
 expect(screen.getByText('Recent successful update')).toBeTruthy();
 expect(screen.getByText('Sync error')).toBeTruthy();
 expect(screen.getByText('Every 6 hours')).toBeTruthy();
 expect(screen.getByText('Queue dispatch failed')).toBeTruthy();
 expect(api).toHaveBeenCalledWith('/intelligence/sources');
});
