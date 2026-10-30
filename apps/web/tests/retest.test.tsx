import React from 'react';
import {render,screen,cleanup,waitFor,act} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import RetestPanel from '../app/console/RetestPanel';
afterEach(cleanup);
const pending={paths:['/','/help'],id:'saved-change',status:'awaiting_approval',created:1,evidence:'Configured headers on staging',rollback_plan:'Restore reviewed config backup',staging_validation:'Navigation and form tests passed',job_id:null,job_status:null,comparison:{},report_available:false};
it('recovers evidence and approval target without manually copying identifiers',async()=>{
 const api=vi.fn(async(p:string,m?:string)=>p.endsWith('/retests')?[pending]:p.endsWith('/authorize')?{id:'auth'}:{job_id:'job'});
 render(<RetestPanel api={api} requestId="request" assetId="asset" onUpdate={vi.fn()} role="owner"/>);
 const user=userEvent.setup();await user.click(screen.getByText('Review change & full security retest'));
 expect(await screen.findByText(pending.rollback_plan)).toBeTruthy();
 const button=screen.getByRole('button',{name:'Approve & run full reassessment'}) as HTMLButtonElement;
 expect(button.disabled).toBe(true);expect(screen.queryByLabelText('Pending retest ID')).toBeNull();
 await user.click(screen.getByRole('checkbox'));await user.click(button);
 expect(api).toHaveBeenCalledWith('/assets/asset/authorize','POST',{accepted:true,hours:24,paths:['/','/help']});
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/retests/saved-change/approve','POST',{accepted:true,authorization_id:'auth'}));
});
it('viewer can read evidence but cannot approve or record changes',async()=>{
 render(<RetestPanel api={vi.fn(async()=>[pending])} requestId="r" assetId="a" onUpdate={vi.fn()} role="viewer"/>);
 await userEvent.click(screen.getByText('Review change & full security retest'));
 expect(await screen.findByText(pending.evidence)).toBeTruthy();
 expect(screen.queryByRole('checkbox')).toBeNull();expect(screen.queryByRole('textbox')).toBeNull();
});
it('ignores late responses from the previous remediation request',async()=>{
 let finish!:(value:unknown)=>void;
 const old=new Promise(resolve=>{finish=resolve});
 const api=vi.fn((p:string)=>p.includes('/old/')?old:Promise.resolve([]));
 const {rerender}=render(<RetestPanel api={api} requestId="old" assetId="a" onUpdate={vi.fn()} role="owner"/>);
 rerender(<RetestPanel api={api} requestId="new" assetId="b" onUpdate={vi.fn()} role="owner"/>);
 await userEvent.click(screen.getByText('Review change & full security retest'));
 await screen.findByText('No recorded changes or retests yet.');
 await act(async()=>{finish([pending]);await old;});
 await waitFor(()=>expect(screen.queryByText(pending.evidence)).toBeNull());
 expect(screen.queryByRole('button',{name:'Approve & run full reassessment'})).toBeNull();
});
it('does not show a late plan after switching request identity',async()=>{
 let finish!:(value:unknown)=>void;const delayed=new Promise(resolve=>{finish=resolve});
 const api=vi.fn((p:string)=>p.endsWith('/old/plan')?delayed:Promise.resolve([]));
 const {rerender}=render(<RetestPanel api={api} requestId="old" assetId="a" onUpdate={vi.fn()} role="owner"/>);
 await userEvent.click(screen.getByText('Review change & full security retest'));
 await userEvent.click(screen.getByRole('button',{name:'Retrieve remediation plan'}));
 rerender(<RetestPanel api={api} requestId="new" assetId="b" onUpdate={vi.fn()} role="owner"/>);
 await act(async()=>{finish({original_finding:{supported_configuration_fix:'OLD REQUEST PRIVATE PLAN'},plan:{},source_code_access:'none'});await delayed;});
 expect(screen.queryByText('OLD REQUEST PRIVATE PLAN')).toBeNull();
});
