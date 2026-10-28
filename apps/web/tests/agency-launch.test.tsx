import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import AgencyPanel from '../app/console/AgencyPanel';
import LaunchPanel from '../app/console/LaunchPanel';
afterEach(cleanup);
it('agency delegation resets consent when report privileges change',async()=>{
 const api=vi.fn(async()=>[]);render(<AgencyPanel api={api} org="client" role="owner"/>);
 await userEvent.type(screen.getByLabelText('Agency workspace ID'),'agency');
 await userEvent.click(screen.getByLabelText(/I authorize this agency/));
 await userEvent.click(screen.getByLabelText('Allow branded assessment report exports'));
 expect((screen.getByText('Authorize agency access') as HTMLButtonElement).disabled).toBe(true);
 await userEvent.click(screen.getByLabelText(/I authorize this agency/));await userEvent.click(screen.getByText('Authorize agency access'));
 expect(api).toHaveBeenCalledWith('/organizations/client/agency-grant','PUT',{agency_id:'agency',accepted:true,reports:true,days:7});
});
it('viewer cannot configure branding or delegation',()=>{
 render(<AgencyPanel api={vi.fn(async()=>[])} org="o" role="viewer"/>);
 expect(screen.queryByText('Save report branding')).toBeNull();expect(screen.queryByText('Authorize agency access')).toBeNull();
});
it('launch review needs fresh consent after PR changes',async()=>{
 const api=vi.fn(async(p:string)=>p.endsWith('/github')?[{id:'c',login:'owner',revoked:false}]:[]);
 render(<LaunchPanel api={api} org="o"/>);
 await userEvent.selectOptions(await screen.findByLabelText('Your GitHub connection'),'c');
 await userEvent.type(screen.getByLabelText('Repository owner/name'),'owned/site');
 await userEvent.click(screen.getByLabelText(/I authorize read-only/));
 await userEvent.clear(screen.getByLabelText('Pull request number'));await userEvent.type(screen.getByLabelText('Pull request number'),'2');
 expect((screen.getByText('Review release evidence') as HTMLButtonElement).disabled).toBe(true);
});
