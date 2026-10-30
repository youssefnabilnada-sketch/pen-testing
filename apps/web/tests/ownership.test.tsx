import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import OwnershipGuide from '../app/console/OwnershipGuide';
afterEach(cleanup);
it('recovers a challenge and prepares a link without claiming verification',async()=>{
 const c={id:'c',method:'file',token:'proof',instruction:'Publish proof',expires:2000000000};
 const api=vi.fn(async(p:string,m?:string)=>p.endsWith('/github')?{url:'https://github.com/owner/site/new/main'}:c);
 const done=vi.fn(async()=>{});render(<OwnershipGuide assetId="a" api={api} onVerified={done}/>);
 expect(await screen.findByText('Publish proof')).toBeTruthy();
 const user=userEvent.setup();await user.click(screen.getByText('My website deploys from GitHub'));
 await user.type(screen.getByLabelText('Repository (owner/name)'),'owner/site');
 await user.click(screen.getByRole('button',{name:'Prepare GitHub file'}));
 expect(await screen.findByRole('link',{name:/Open prepared/})).toBeTruthy();
 expect(done).not.toHaveBeenCalled();
 await user.click(screen.getByRole('button',{name:'Check ownership'}));
 expect(done).toHaveBeenCalledOnce();
});
it('shows service failure without a success claim',async()=>{
 const api=vi.fn(async()=>{throw new Error('Verification unavailable')});
 render(<OwnershipGuide assetId="a" api={api} onVerified={vi.fn()}/>);
 expect((await screen.findByRole('alert')).textContent).toBe('Verification unavailable');
});
it.each(['file','dns','meta'])('explains %s verification without granting assessment permission',async(method)=>{
 const challenge={id:'c',method,token:'proof',instruction:'Exact server instructions',expires:2000000000};
 const api=vi.fn(async(p:string)=>p.endsWith('/verification-recommendation')?null:challenge);
 const done=vi.fn(async()=>{});render(<OwnershipGuide assetId="a" api={api} onVerified={done}/>);
 await screen.findByText('Exact server instructions');
 expect(screen.getByText(/Return here and choose Check ownership/)).toBeTruthy();
 expect(api.mock.calls.some(([p])=>p.includes('/verify/'))).toBe(false);
 expect(done).not.toHaveBeenCalled();
});
