import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import PageDiscovery from '../app/console/PageDiscovery';
afterEach(cleanup);
it('requires discovery consent and separately selects paths without launching scans',async()=>{
 const api=vi.fn(async()=>({paths:['/','/help','/about','/contact']})),select=vi.fn();render(<PageDiscovery assetId="a" verified api={api} onSelect={select}/>);
 const user=userEvent.setup();expect((screen.getByRole('button',{name:'Discover pages'}) as HTMLButtonElement).disabled).toBe(true);
 await user.click(screen.getByLabelText(/I authorize one GET/));await user.click(screen.getByRole('button',{name:'Discover pages'}));await screen.findByText('4 candidate paths. Select up to three.');
 expect(select).not.toHaveBeenCalled();for(const p of ['/','/help','/about'])await user.click(screen.getByLabelText(p,{exact:true}));
 expect((screen.getByLabelText('/contact') as HTMLInputElement).disabled).toBe(true);await user.click(screen.getByRole('button',{name:'Use selected paths for review'}));
 expect(select).toHaveBeenCalledWith(['/','/help','/about']);expect(api).toHaveBeenCalledTimes(1);
});
it('disables discovery without verified ownership',()=>{
 render(<PageDiscovery assetId="a" verified={false} api={vi.fn()} onSelect={vi.fn()}/>);
 expect((screen.getByLabelText(/I authorize one GET/) as HTMLInputElement).disabled).toBe(true);
});
