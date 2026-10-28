import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import CrmPanel from '../app/console/CrmPanel';
afterEach(cleanup);
it('withdraws contact consent explicitly and reloads the saved state',async()=>{
 let consent=true;
 const api=vi.fn(async(p:string,m?:string)=>{
  if(m==='POST'){consent=false;return {contact_consent:false,message_sent:false}}
  return [{id:'lead',kind:'demo',status:'new',contact_consent:consent}];
 });
 render(<CrmPanel api={api} org="workspace"/>);
 await userEvent.click(await screen.findByRole('button',{name:'Withdraw contact consent'}));
 expect(api).toHaveBeenCalledWith('/organizations/workspace/crm-requests/lead/withdraw-consent','POST');
 expect(await screen.findByRole('status')).toHaveProperty('textContent','Contact consent withdrawn. Follow-up reminders cancelled.');
 expect(screen.queryByRole('button',{name:'Withdraw contact consent'})).toBeNull();
});
it('does not claim withdrawal succeeded when the server rejects it',async()=>{
 const api=vi.fn(async(p:string,m?:string)=>{
  if(m==='POST')throw new Error('Workspace access revoked.');
  return [{id:'lead',kind:'demo',status:'new',contact_consent:true}];
 });
 render(<CrmPanel api={api} org="workspace"/>);
 await userEvent.click(await screen.findByRole('button',{name:'Withdraw contact consent'}));
 expect(await screen.findByRole('alert')).toHaveProperty('textContent','Workspace access revoked.');
 expect(screen.queryByRole('status')).toBeNull();
 expect(screen.getByRole('button',{name:'Withdraw contact consent'})).toBeTruthy();
});
