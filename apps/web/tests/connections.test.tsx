import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {it,expect,afterEach,vi} from 'vitest';
import ConnectionsPanel from '../app/console/ConnectionsPanel';
afterEach(cleanup);
it('does not claim a connection until a real diagnostic response is requested',async()=>{
 const api=vi.fn(async()=>({ready:false,checked_at:1,database:{status:'migration_required',engine:'postgresql',schema_current:false},queue:{status:'unavailable',pending_assessments:null},firebase:{status:'unavailable',connected:false},email:{status:'unavailable',delivery_tested:false},workers:{status:'unavailable',scanner_available:false,intelligence_available:false},payments_enabled:false}));
 render(<ConnectionsPanel api={api}/>);
 expect(api).not.toHaveBeenCalled();expect(screen.getByText(/No connection check performed/)).toBeTruthy();
 await userEvent.click(screen.getByRole('button',{name:'Check actual connections'}));
 expect((await screen.findByRole('status')).textContent).toContain('not verified');
 expect(screen.getByText('Pending assessments: Unknown')).toBeTruthy();
 expect(screen.getByText('Pending email notifications: Unknown')).toBeTruthy();
 expect(screen.getByText('Notification worker')).toBeTruthy();
 expect(screen.getByText(/No — apply migrations/)).toBeTruthy();
});
it('reports server errors without a success banner',async()=>{
 render(<ConnectionsPanel api={async()=>{throw new Error('Workspace permission required.')}}/>);
 await userEvent.click(screen.getByRole('button',{name:'Check actual connections'}));
 expect((await screen.findByRole('alert')).textContent).toContain('permission');
 expect(screen.queryByText('Required service connections responded.')).toBeNull();
});

it('shows the notification worker without claiming inbox delivery',async()=>{
 render(<ConnectionsPanel api={async()=>({ready:true,checked_at:1,
  database:{status:'ready',engine:'postgresql',schema_current:true},
  queue:{status:'ready',pending_assessments:0,pending_notifications:2},
  firebase:{status:'ready',connected:true,project:'fixture'},
  email:{status:'ready',delivery_tested:false},
  workers:{status:'ready',scanner_available:true,intelligence_available:true,notifier_available:true},
  payments_enabled:false})}/>);
 await userEvent.click(screen.getByRole('button',{name:'Check actual connections'}));
 expect((await screen.findByRole('status')).textContent).toContain('Required service connections');
 expect(screen.getByText('Pending email notifications: 2')).toBeTruthy();
 expect(screen.getByText('Notification worker')).toBeTruthy();
 expect(screen.getByText(/Email delivery to an inbox is not verified/)).toBeTruthy();
});
