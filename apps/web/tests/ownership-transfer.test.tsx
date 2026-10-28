import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,afterEach,vi} from 'vitest';
import OwnershipTransferPanel from '../app/console/OwnershipTransferPanel';
afterEach(cleanup);
it('requires selection and consent before submitting confirmed ownership',async()=>{
 const api=vi.fn(async()=>[{id:'u',email:'admin@example.test',role:'admin'}]),done=vi.fn(async()=>{});
 render(<OwnershipTransferPanel api={api} org="o" onTransferred={done}/>);
 await userEvent.selectOptions(await screen.findByLabelText('New organization owner'),'u');
 expect((screen.getByText('Confirm ownership transfer') as HTMLButtonElement).disabled).toBe(true);
 await userEvent.type(screen.getByLabelText('Type the new owner’s email'),'admin@example.test');await userEvent.type(screen.getByLabelText('Your current password'),'Long-password123!');await userEvent.click(screen.getByLabelText('I authorize this ownership transfer and understand my owner role will end.'));await userEvent.click(screen.getByText('Confirm ownership transfer'));
 expect(done).toHaveBeenCalledOnce();expect(api).toHaveBeenCalledWith('/organizations/o/transfer-ownership','POST',{target_user_id:'u',confirm_email:'admin@example.test',current_password:'Long-password123!',mfa_code:'',confirm_transfer:true});
});
