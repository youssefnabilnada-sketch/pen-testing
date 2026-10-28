import React from 'react';
import {render,screen,cleanup,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import RepositoryControl from '../app/console/RepositoryControl';
afterEach(cleanup);
it('reads actual pause state and persists explicit publication control',async()=>{
 const api=vi.fn(async(p:string,m?:string)=>({paused:m==='POST'}));
 render(<RepositoryControl api={api}/>);
 await screen.findByText('Reviewed pull request publication is enabled');
 await userEvent.click(screen.getByRole('button',{name:'Pause new publication'}));
 await waitFor(()=>expect(api).toHaveBeenCalledWith('/admin/repository-control','POST',{accepted:true}));
 expect(await screen.findByText('New pull request publication is paused')).toBeTruthy();
});
it('fails closed in the UI when state cannot be loaded',async()=>{
 render(<RepositoryControl api={async()=>{throw new Error('Unavailable')}}/>);
 expect(await screen.findByRole('alert')).toBeTruthy();
 expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
});
