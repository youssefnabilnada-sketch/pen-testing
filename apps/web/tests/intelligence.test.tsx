import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import IntelligencePanel from '../app/console/IntelligencePanel';
import RetestPanel from '../app/console/RetestPanel';
afterEach(cleanup);
const api=vi.fn(async(path:string)=>path.includes('/organizations/')?{inventory:[],impacts:[],notifications:[],schedules:[],retests:[]}:path.endsWith('/rules')?{built_in:[],candidates:[]}:[]);
it('separates advisory data and requires monitoring consent',async()=>{
 render(<IntelligencePanel api={api} org="org" assets={[{id:'a',origin:'https://fixture.test',verified:true}]} isAdmin={false}/>);
 expect(screen.getByText(/Package\/version matches do not establish runtime exploitability/)).toBeTruthy();
 const user=userEvent.setup();await user.click(screen.getByRole('button',{name:'Monitoring'}));
 await user.selectOptions(screen.getByLabelText('Customer asset'),'a');
 expect((screen.getByRole('button',{name:'Approve monitoring schedule'}) as HTMLButtonElement).disabled).toBe(true);
 await user.click(screen.getByLabelText(/I authorize recurring/));
 expect((screen.getByRole('button',{name:'Approve monitoring schedule'}) as HTMLButtonElement).disabled).toBe(false);
 await user.click(screen.getByRole('button',{name:'Approve monitoring schedule'}));
 expect(api).toHaveBeenCalledWith('/assets/a/schedule','POST',{paths:['/'],cadence:'weekly',consent_days:30,accepted:true,on_advisory:false,reverify:true,start_hour_utc:0,end_hour_utc:24});
 await user.selectOptions(screen.getByLabelText('Frequency'),'daily');
 expect((screen.getByRole('button',{name:'Approve monitoring schedule'}) as HTMLButtonElement).disabled).toBe(true);
});
it('shows source failure without success',async()=>{
 render(<IntelligencePanel api={async()=>{throw new Error('Source unavailable')}} org="org" assets={[]} isAdmin={false}/>);
 expect((await screen.findByRole('alert')).textContent).toBe('Source unavailable');
});
it('cannot launch reassessment without a recorded pending change',async()=>{
 const call=vi.fn(async()=>[]);render(<RetestPanel role="owner" api={call} requestId="r" assetId="a" onUpdate={async()=>{}}/>);
 const user=userEvent.setup();await user.click(screen.getByText('Review change & full security retest'));
 expect(await screen.findByText('No recorded changes or retests yet.')).toBeTruthy();
 expect(screen.getByText(/This page does not modify your website/)).toBeTruthy();
 expect(screen.queryByRole('button',{name:'Approve & run full reassessment'})).toBeNull();
 expect(call).toHaveBeenCalledWith('/remediations/r/retests');
});
it('requires explicit per-detector review and refreshes activation state',async()=>{
 const call=vi.fn(async(path:string)=>path.includes('/organizations/')?{inventory:[],impacts:[],notifications:[],schedules:[],retests:[]}:path.endsWith('/rules')?{built_in:[],candidates:[{key:'csp.base-uri',title:'Base URI',version:'1',enabled:false}]}:[]);
 render(<IntelligencePanel api={call} org="org" assets={[]} isAdmin/>);
 const user=userEvent.setup();await user.click(screen.getByRole('button',{name:'Knowledge'}));
 await user.click(await screen.findByRole('button',{name:'validate csp.base-uri'}));
 expect(call).toHaveBeenCalledWith('/admin/intelligence/rules/csp.base-uri/validate','POST');
 expect(call).not.toHaveBeenCalledWith('/admin/intelligence/rules/csp.base-uri/approve','POST');
 await user.click(await screen.findByRole('button',{name:'approve csp.base-uri'}));
 expect(call).toHaveBeenCalledWith('/admin/intelligence/rules/csp.base-uri/approve','POST');
 await user.click(await screen.findByRole('button',{name:'disable csp.base-uri'}));
 expect(call).toHaveBeenCalledWith('/admin/intelligence/rules/csp.base-uri/disable','POST');
});

it('clears consent after recurring scope paths change',async()=>{
 render(<IntelligencePanel api={api} org="org" assets={[{id:'a',origin:'https://fixture.test',verified:true}]} isAdmin={false}/>);
 const user=userEvent.setup();await user.click(screen.getByRole('button',{name:'Monitoring'}));
 await user.selectOptions(screen.getByLabelText('Customer asset'),'a');await user.click(screen.getByLabelText(/I authorize recurring/));
 await user.type(screen.getByLabelText(/Recurring assessment paths/),'\n/help');
 expect((screen.getByRole('button',{name:'Approve monitoring schedule'}) as HTMLButtonElement).disabled).toBe(true);
 await user.click(screen.getByLabelText(/I authorize recurring/));await user.click(screen.getByRole('button',{name:'Approve monitoring schedule'}));
 expect(api).toHaveBeenCalledWith('/assets/a/schedule','POST',expect.objectContaining({paths:['/','/help'],accepted:true}));
});
