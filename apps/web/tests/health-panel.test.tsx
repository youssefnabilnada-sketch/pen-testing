import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import HealthPanel from '../app/console/HealthPanel';
afterEach(cleanup);
const assets=[{id:'a',origin:'https://owned.example',verified:true}];
it('requires renewed consent for scope changes and saves the approved monitor',async()=>{
 const api=vi.fn(async()=>[]),user=userEvent.setup();
 render(<HealthPanel api={api} org="o" assets={assets} canManage/>);
 await user.selectOptions(screen.getByLabelText('Verified website'),'a');
 const button=screen.getByRole('button',{name:'Authorize health monitoring'}) as HTMLButtonElement;
 expect(button.disabled).toBe(true);
 await user.click(screen.getByLabelText(/I authorize one bounded/));
 await user.type(screen.getByLabelText('Approved health path'),'health');
 expect(button.disabled).toBe(true);
 await user.click(screen.getByLabelText(/I authorize one bounded/));await user.click(button);
 expect(api).toHaveBeenCalledWith('/assets/a/health-monitor','PUT',{accepted:true,path:'/health',interval_seconds:900,hours:24});
});
it('shows history to viewers without mutation controls',async()=>{
 const api=vi.fn(async(p:string)=>p.endsWith('/samples')?[]:[{id:'m',origin:'https://owned.example',enabled:true,last_status:'up',expires:2000000000}]);
 render(<HealthPanel api={api} org="o" assets={assets}/>);
 await userEvent.click(await screen.findByText('View history'));
 expect(api).toHaveBeenCalledWith('/health-monitors/m/samples');
 expect(screen.queryByText('Disable monitor')).toBeNull();
 expect(screen.queryByText('Authorize health monitoring')).toBeNull();
});
it('shows authorization failure without claiming a monitor was enabled',async()=>{
 const api=vi.fn(async(p:string,m?:string)=>{if(m==='PUT')throw new Error('Ownership expired');return []});
 render(<HealthPanel api={api} org="o" assets={assets} canManage/>);
 await userEvent.selectOptions(screen.getByLabelText('Verified website'),'a');
 await userEvent.click(screen.getByLabelText(/I authorize one bounded/));
 await userEvent.click(screen.getByText('Authorize health monitoring'));
 expect((await screen.findByRole('alert')).textContent).toContain('Ownership expired');
});
