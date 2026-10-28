import React from 'react';
import {render,screen,cleanup,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import OperationsPanel from '../app/console/OperationsPanel';
afterEach(cleanup);
const summary={checked_at:1,organizations:1,users:1,assets:0,verified_assets:0,outbox_pending:0,outbox_retrying:0,jobs:{},schedules:{},sources:[],storage:'Recorded snapshots',ai_mode:'Deterministic'};
it('paginates and refreshes real records',async()=>{
 const api=vi.fn(async(path:string)=>path==='/admin/operations'?summary:{total:26,items:[{id:path.includes('offset=25')?'second-page':'first-page',status:'failed'}]});
 render(<OperationsPanel api={api}/>);const user=userEvent.setup();
 expect(await screen.findByText('No assessment jobs recorded.')).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Next records'}));
 expect(await screen.findByText('second-page · failed')).toBeTruthy();
 await user.selectOptions(screen.getByLabelText('Record type'),'users');
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/admin/operations/records/users?offset=0&limit=25'));
 await user.click(screen.getByRole('button',{name:'Refresh operations'}));
 expect(api.mock.calls.filter(([p])=>p==='/admin/operations').length).toBeGreaterThan(2);
});
it('shows failed loading instead of empty success',async()=>{
 render(<OperationsPanel api={async()=>{throw new Error('Service unavailable')}}/>);
 expect((await screen.findByRole('alert')).textContent).toBe('Service unavailable');
 expect(screen.queryByText('No assessment jobs recorded.')).toBeNull();
});
