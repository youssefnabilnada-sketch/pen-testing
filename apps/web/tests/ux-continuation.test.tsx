import {render,screen,fireEvent,cleanup,act} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import EmailHistory from '../app/console/EmailHistory';
import FastFixGuidance from '../app/console/FastFixGuidance';
import OwnershipGuide from '../app/console/OwnershipGuide';
import {Experience} from '../app/console/Experience';
afterEach(()=>{cleanup();localStorage.clear()});
it('discards an email response from a previous workspace',async()=>{
 let finish!:(value:any)=>void;
 const api=vi.fn(()=>new Promise(resolve=>{finish=resolve}));
 const view=render(<EmailHistory api={api} org="first"/>);
 fireEvent.click(screen.getByText('Refresh email history'));
 view.rerender(<EmailHistory api={api} org="second"/>);
 await act(async()=>finish([{id:'private',title:'Previous workspace message',status:'smtp_accepted',attempts:1}]));
 expect(screen.queryByText(/Previous workspace message/)).toBeNull();
});
it('offers the existing Netlify guidance without publishing changes',async()=>{
 const api=vi.fn(async(_path:string)=>({mode:'guidance',compatibility_risks:[],validation_required:[]}));
 render(<FastFixGuidance api={api} findingId="f"/>);
 fireEvent.click(screen.getByText('Choose a remediation path'));
 fireEvent.change(screen.getByLabelText(/Your platform/),{target:{value:'netlify'}});
 await screen.findByText('Guidance only · no change applied');
 expect(api).toHaveBeenLastCalledWith('/findings/f/fastfix?platform=netlify');
 expect(api.mock.calls.every(call=>call.length===1)).toBe(true);
});
it('translates ownership controls without creating or verifying a challenge',async()=>{
 const api=vi.fn(async()=>null);
 render(<Experience><OwnershipGuide assetId="a" api={api} onVerified={vi.fn()}/></Experience>);
 await act(async()=>{});
 const count=api.mock.calls.length;
 fireEvent.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));
 expect(screen.getByRole('button',{name:'عرض خطوات التحقق'})).toBeTruthy();
 expect(screen.getByLabelText('طريقة إثبات الملكية')).toBeTruthy();
 expect(api.mock.calls.length).toBe(count);
});
