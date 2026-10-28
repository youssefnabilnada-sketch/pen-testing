import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,afterEach,vi} from 'vitest';
import MfaPanel from '../app/console/MfaPanel';
afterEach(cleanup);
it('requires confirmation before enabling and displays recovery codes once',async()=>{
 let enabled=false;
 const api=vi.fn(async(p:string)=>{if(p.endsWith('/setup'))return {secret:'TESTSEED'};if(p.endsWith('/confirm')){enabled=true;return {recovery_codes:['recovery-fixture']}}return {enabled,setup_available:true}});
 render(<MfaPanel api={api} onDisabled={()=>{}}/>);
 await userEvent.type(await screen.findByLabelText('Current AEGIS password'),'Long-password123!');
 await userEvent.click(screen.getByText('Set up authenticator'));
 expect(await screen.findByText('TESTSEED')).toBeTruthy();expect(screen.getByText('Authenticator not enabled')).toBeTruthy();
 await userEvent.type(screen.getByLabelText('Six-digit code'),'123456');await userEvent.click(screen.getByText('Confirm authenticator'));
 expect(await screen.findByText('recovery-fixture')).toBeTruthy();expect(await screen.findByText('Authenticator enabled')).toBeTruthy();
 await userEvent.click(screen.getByText('I saved my recovery codes'));expect(screen.queryByText('recovery-fixture')).toBeNull();
});
it('disables enrollment when server encryption is unavailable',async()=>{
 render(<MfaPanel api={async()=>({enabled:false,setup_available:false})} onDisabled={()=>{}}/>);
 expect((await screen.findByText('Set up authenticator') as HTMLButtonElement).disabled).toBe(true);
});
it('signs out after disable without using the revoked session again',async()=>{
 const done=vi.fn(),api=vi.fn(async()=>({enabled:true,setup_available:true}));
 render(<MfaPanel api={api} onDisabled={done}/>);
 await userEvent.type(await screen.findByLabelText('Current AEGIS password'),'Long-password123!');await userEvent.type(screen.getByLabelText('New authenticator or unused recovery code'),'123456');
 await userEvent.click(screen.getByText('Disable authenticator & sign out'));expect(done).toHaveBeenCalledOnce();expect(api).toHaveBeenCalledTimes(2);
});
