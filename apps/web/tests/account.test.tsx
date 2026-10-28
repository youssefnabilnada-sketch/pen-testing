import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,afterEach,vi} from 'vitest';
import AccountPanel from '../app/console/AccountPanel';
afterEach(cleanup);
it('saves a display name through the authenticated API',async()=>{
 const api=vi.fn(async()=>({display_name:'Analyst'}));
 render(<AccountPanel api={api} onSignedOut={()=>{}}/>);
 await userEvent.clear(await screen.findByLabelText('Display name'));await userEvent.type(screen.getByLabelText('Display name'),'Engineer');await userEvent.click(screen.getByText('Save display name'));
 expect((await screen.findByRole('status')).textContent).toContain('saved');expect(api).toHaveBeenCalledWith('/auth/account','PATCH',{display_name:'Engineer'});
});
it('requires explicit deactivation confirmation and displays server refusal',async()=>{
 const out=vi.fn(),api=vi.fn(async(p:string,m?:string)=>{if(m==='POST')throw new Error('An organization owner cannot deactivate.');return {display_name:'Owner'}});
 render(<AccountPanel api={api} onSignedOut={out}/>);
 await userEvent.selectOptions(await screen.findByLabelText('Account action'),'deactivate');
 expect((screen.getByText('Confirm account action') as HTMLButtonElement).disabled).toBe(true);
 await userEvent.type(screen.getByLabelText('Confirm your current password'),'Long-password123!');await userEvent.click(screen.getByLabelText('I understand my account will be disabled and I will be signed out.'));await userEvent.click(screen.getByText('Confirm account action'));
 expect((await screen.findByRole('alert')).textContent).toContain('cannot deactivate');expect(out).not.toHaveBeenCalled();
});
