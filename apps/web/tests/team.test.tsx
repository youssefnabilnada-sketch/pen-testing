import React from 'react';
import {render,screen,cleanup,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import TeamPanel,{IncomingInvitations} from '../app/console/TeamPanel';
afterEach(cleanup);
it('requires explicit acceptance of the displayed incoming workspace',async()=>{
 const api=vi.fn(async(path:string)=>path.endsWith('incoming')?[{id:'inv',organization:'Inviting company',role:'viewer',expires:2000000000}]:{}),done=vi.fn(async()=>{});
 render(<IncomingInvitations api={api} onAccepted={done}/>);
 expect(api).not.toHaveBeenCalled();await userEvent.click(screen.getByText('Check my invitations'));
 expect(await screen.findByText('Inviting company')).toBeTruthy();expect(done).not.toHaveBeenCalled();
 await userEvent.click(screen.getByText('Accept invitation'));await waitFor(()=>expect(done).toHaveBeenCalledOnce());
 expect(api).toHaveBeenCalledWith('/invitations/inv/accept','POST');
});
it('does not show invitation controls to read-only members',async()=>{
 const api=vi.fn(async()=>[{id:'u',email:'owner@example.test',role:'owner'}]);
 render(<TeamPanel api={api} orgId="org" role="viewer"/>);
 expect(await screen.findByText('owner@example.test')).toBeTruthy();
 expect(screen.queryByText('Send invitation')).toBeNull();expect(api).not.toHaveBeenCalledWith('/organizations/org/invitations');
});
it('shows email failure without claiming an invitation was sent',async()=>{
 const api=vi.fn(async(path:string,method?:string)=>{if(method==='POST')throw new Error('Invitation email could not be sent.');return []});
 render(<TeamPanel api={api} orgId="org" role="owner"/>);
 await userEvent.type(screen.getByLabelText('Invitation email'),'new@example.test');await userEvent.click(screen.getByText('Send invitation'));
 expect((await screen.findByRole('alert')).textContent).toContain('could not be sent');expect(screen.queryByRole('status')).toBeNull();
});
