import React from 'react';
import {render,screen,cleanup,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import FindingsPanel from '../app/console/FindingsPanel';
afterEach(cleanup);
const finding={id:'f',title:'Fixture observation',rule:'fixture',origin:'https://fixture.test',severity:'low',confidence:'high',status:'open',evidence:'Observed header',remediation:'Review'};
it('searches server data and prevents viewer mutations',async()=>{
 const api=vi.fn(async(path:string)=>path.includes('/history')?{total:1,items:[{id:'h',status:'open',created:1,job_id:'j'}]}:{total:26,items:[finding]});
 render(<FindingsPanel api={api} org="o" role="viewer" onRemediation={async()=>{}}/>);const user=userEvent.setup();
 expect(await screen.findByText('Fixture observation')).toBeTruthy();
 expect(screen.queryByRole('button',{name:'Request remediation'})).toBeNull();
 await user.click(screen.getByRole('button',{name:'Next findings'}));
 await waitFor(()=>expect(api.mock.calls.some(([p])=>p.includes('offset=25'))).toBe(true));
 await user.type(screen.getByLabelText('Search observations'),'CSP');
 await user.click(screen.getByRole('button',{name:'Search all findings'}));
 await waitFor(()=>expect(api.mock.calls.some(([p])=>p.includes('q=CSP')&&p.includes('offset=0'))).toBe(true));
 await user.click(await screen.findByRole('button',{name:'History · Fixture observation'}));
 expect(await screen.findByText('1 recorded events')).toBeTruthy();
});
it('retains backend failures without showing an empty clean result',async()=>{
 render(<FindingsPanel api={async()=>{throw new Error('Findings unavailable')}} org="o" role="owner" onRemediation={async()=>{}}/>);
 expect((await screen.findByRole('alert')).textContent).toBe('Findings unavailable');
 expect(screen.queryByText('No observations match these filters.')).toBeNull();
});
it('requests remediation for an analyst',async()=>{
 const api=vi.fn(async()=>({total:1,items:[finding]}));const done=vi.fn(async()=>{});
 render(<FindingsPanel api={api} org="o" role="analyst" onRemediation={done}/>);
 await userEvent.click(await screen.findByRole('button',{name:'Request remediation'}));
 expect(api).toHaveBeenCalledWith('/remediations','POST',{finding_id:'f'});expect(done).toHaveBeenCalled();
});
