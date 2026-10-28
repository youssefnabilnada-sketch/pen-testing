import React from 'react';
import {render,screen,cleanup,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import FirebasePanel from '../app/console/FirebasePanel';
const mocks=vi.hoisted(()=>({authenticate:vi.fn(),reset:vi.fn()}));
vi.mock('../lib/firebase-client',()=>({authenticate:mocks.authenticate,resetFirebasePassword:mocks.reset,friendlyError:(e:Error)=>e.message}));
afterEach(cleanup);
beforeEach(()=>vi.clearAllMocks());
const config={enabled:true,config:{projectId:'fixture'}};
it('hides Firebase login when disabled',async()=>{
 const api=vi.fn(async()=>({enabled:false}));const {container}=render(<FirebasePanel api={api} onComplete={vi.fn()}/>);
 await waitFor(()=>expect(api).toHaveBeenCalled());expect(container.textContent).toBe('');
});
it('creates only with explicit mode and recovery password before session exchange',async()=>{
 mocks.authenticate.mockImplementation(async(c,p,e,pw,create,exchange)=>exchange('fresh-id-token'));
 const api=vi.fn(async(p:string)=>p.endsWith('/config')?config:{}),done=vi.fn(async()=>{});
 render(<FirebasePanel api={api} onComplete={done}/>);const user=userEvent.setup();
 await screen.findByText('Continue with Firebase');
 await user.selectOptions(screen.getByLabelText('Firebase action'),'create');
 expect((screen.getByRole('button',{name:'Continue with Google'}) as HTMLButtonElement).disabled).toBe(true);
 await user.type(screen.getByLabelText(/New AEGIS recovery/),'Recovery-password123!');
 await user.click(screen.getByRole('button',{name:'Continue with Google'}));
 await waitFor(()=>expect(done).toHaveBeenCalledOnce());
 expect(api).toHaveBeenCalledWith('/auth/firebase/register','POST',{id_token:'fresh-id-token',recovery_password:'Recovery-password123!'});
 expect(api).toHaveBeenCalledWith('/auth/firebase/login','POST',{id_token:'fresh-id-token'});
});
it('links only with current AEGIS password and shows provider failure',async()=>{
 mocks.authenticate.mockRejectedValue(new Error('Google sign-in was cancelled.'));
 const api=vi.fn(async(p:string)=>p.endsWith('/config')?config:{linked:false});
 render(<FirebasePanel account api={api} onComplete={vi.fn()}/>);const user=userEvent.setup();
 await screen.findByText('Connected identity');
 const button=screen.getByRole('button',{name:'Link Google identity'}) as HTMLButtonElement;
 expect(button.disabled).toBe(true);
 await user.type(screen.getByLabelText('Current AEGIS password'),'Recovery-password123!');await user.click(button);
 expect((await screen.findByRole('alert')).textContent).toContain('cancelled');
 expect(api.mock.calls.some(c=>c[0].endsWith('/link'))).toBe(false);
});
