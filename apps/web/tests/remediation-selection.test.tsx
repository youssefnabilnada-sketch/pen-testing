import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import RemediationRequestPanel from '../app/console/RemediationRequestPanel';
afterEach(cleanup);
const assets=[{id:'a',origin:'https://fixture.test'}];
it('submits explicit selected scope without claiming a repair',async()=>{
 const api=vi.fn(async()=>({created:1,reused:2,message:'Review requested. No website changes.',estimate:'Preliminary review required'}));const update=vi.fn(async()=>{});
 render(<RemediationRequestPanel api={api} assets={assets} role="owner" onCreated={update}/>);
 const user=userEvent.setup();expect((screen.getByRole('button',{name:'Request engineering review'}) as HTMLButtonElement).disabled).toBe(true);
 await user.selectOptions(screen.getByLabelText('Website for remediation'),'a');await user.selectOptions(screen.getByLabelText('Issues to review'),'critical');await user.click(screen.getByRole('button',{name:'Request engineering review'}));
 expect(api).toHaveBeenCalledWith('/assets/a/request-remediation','POST',{selection:'critical'});expect(update).toHaveBeenCalledOnce();
 expect((await screen.findByRole('status')).textContent).toContain('No website changes');
});
it('shows an empty selection accurately and prevents viewer writes',async()=>{
 const update=vi.fn(async()=>{});const api=vi.fn(async()=>({created:0,reused:0,message:'No eligible findings',estimate:'Review required'}));
 const {unmount}=render(<RemediationRequestPanel api={api} assets={assets} role="analyst" onCreated={update}/>);
 await userEvent.selectOptions(screen.getByLabelText('Website for remediation'),'a');await userEvent.click(screen.getByRole('button',{name:'Request engineering review'}));
 expect(await screen.findByText('No eligible findings')).toBeTruthy();expect(update).not.toHaveBeenCalled();unmount();
 render(<RemediationRequestPanel api={api} assets={assets} role="viewer" onCreated={update}/>);
 expect(screen.queryByRole('button',{name:'Request engineering review'})).toBeNull();
});
it('does not report a request after a backend failure',async()=>{
 render(<RemediationRequestPanel api={async()=>{throw new Error('Request unavailable')}} assets={assets} role="owner" onCreated={async()=>{}}/>);
 await userEvent.selectOptions(screen.getByLabelText('Website for remediation'),'a');await userEvent.click(screen.getByRole('button',{name:'Request engineering review'}));
 expect((await screen.findByRole('alert')).textContent).toBe('Request unavailable');expect(screen.queryByRole('status')).toBeNull();
});
