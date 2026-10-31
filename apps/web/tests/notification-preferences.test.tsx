import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,afterEach,vi} from 'vitest';
import NotificationPreferences from '../app/console/NotificationPreferences';
afterEach(cleanup);
it('saves personal categories and refreshes the alert list',async()=>{
 const api=vi.fn(async()=>({enabled_kinds:['assessment_failed']})),refresh=vi.fn(async()=>{});
 render(<NotificationPreferences api={api} org="o" onSaved={refresh}/>);
 await userEvent.click(await screen.findByLabelText('Relevant advisories'));await userEvent.click(screen.getByText('Save notification preferences'));
 expect(await screen.findByRole('status')).toBeTruthy();expect(api).toHaveBeenCalledWith('/organizations/o/notification-preferences','PUT',{enabled_kinds:['assessment_failed','advisory_impact']});expect(refresh).toHaveBeenCalledOnce();
});
it('reports save failure without claiming success',async()=>{
 const api=vi.fn(async(p:string,m?:string)=>{if(m==='PUT')throw new Error('Permission changed');return {enabled_kinds:[]}});
 render(<NotificationPreferences api={api} org="o" onSaved={async()=>{}}/>);
 await userEvent.click(await screen.findByText('Save notification preferences'));
 expect((await screen.findByRole('alert')).textContent).toContain('Permission');expect(screen.queryByRole('status')).toBeNull();
});
it('does not show a previous workspace save result after switching organizations',async()=>{
 let finish!:()=>void;
 const api=vi.fn(async(_p:string,m?:string)=>{if(m==='PUT')await new Promise<void>(r=>finish=r);return {enabled_kinds:[]}});
 const props={api,onSaved:async()=>{}};
 const view=render(<NotificationPreferences {...props} org="first"/>);
 await userEvent.click(await screen.findByText('Save notification preferences'));
 view.rerender(<NotificationPreferences {...props} org="second"/>);
 await screen.findByText('Save notification preferences');
 finish();
 await new Promise(r=>setTimeout(r,0));
 expect(screen.queryByText('Your notification preferences were saved.')).toBeNull();
 expect(api).not.toHaveBeenCalledWith('/organizations/second/notification-preferences','PUT',expect.anything());
});
