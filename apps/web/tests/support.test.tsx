import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,afterEach,vi} from 'vitest';
import SupportPanel from '../app/console/SupportPanel';
afterEach(cleanup);
it('lets a viewer read without creating or replying',async()=>{
 const api=vi.fn(async(path:string)=>path.startsWith('/files/')?[]:path.includes('?offset=')?[{id:'t',subject:'Scope question',status:'open'}]:{id:'t',subject:'Scope question',status:'open',messages:[{id:'m',body:'Only safe checks.',staff:true,internal:false,created:1}]});
 render(<SupportPanel api={api} orgId="org" role="viewer"/>);
 await userEvent.click(await screen.findByText('Open Scope question'));
 expect(await screen.findByText('Only safe checks.')).toBeTruthy();expect(screen.queryByText('Create support ticket')).toBeNull();expect(screen.queryByText('Send reply')).toBeNull();
});
it('shows a failed creation without inventing a ticket',async()=>{
 const api=vi.fn(async(p:string,m?:string)=>{if(m==='POST')throw new Error('Service unavailable');return []});
 render(<SupportPanel api={api} orgId="org" role="owner"/>);
 await userEvent.type(screen.getByLabelText('Subject'),'Need help');await userEvent.type(screen.getByLabelText('Your question'),'Question about scope');await userEvent.click(screen.getByText('Create support ticket'));
 expect((await screen.findByRole('alert')).textContent).toContain('unavailable');expect(screen.getByLabelText('Your question')).toBeTruthy();
});
