import React from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RepositoryPanel from '../app/console/RepositoryPanel';
import HealthPanel from '../app/console/HealthPanel';
import WorkspaceNavigation from '../app/console/WorkspaceNavigation';
import WorkspaceToolGuide from '../app/console/WorkspaceToolGuide';
afterEach(cleanup);

it('shows a clear GitHub configuration blocker and safe non-GitHub alternative',async()=>{
 const api=vi.fn(async(path:string,method='GET')=>{
  if(method==='POST'&&path.endsWith('/github/start'))throw new Error('GitHub App configuration is required.');
  return [];
 });
 const open=vi.fn();
 render(<RepositoryPanel api={api} org="fixture" requests={[]} role="owner" onOpenFindings={open}/>);
 const user=userEvent.setup();
 expect(screen.getByText('No GitHub? You can still remediate.')).toBeTruthy();
 expect(screen.getByRole('button',{name:'Connect GitHub securely'})).toHaveProperty('disabled',true);
 await user.click(screen.getByRole('checkbox',{name:/I authorize AEGIS to request access/}));
 await user.click(screen.getByRole('button',{name:'Connect GitHub securely'}));
 expect(await screen.findByText('GitHub integration needs administrator setup')).toBeTruthy();
 expect(screen.getByText(/administrator must configure the app securely/)).toBeTruthy();
 await user.click(screen.getByRole('button',{name:/Open findings and guidance/}));
 expect(open).toHaveBeenCalledOnce();
 expect(api.mock.calls.filter(x=>x[1]==='POST').map(x=>x[0])).toEqual(['/organizations/fixture/github/start']);
});

it('shows monitored assets first, with a separately consented setup',async()=>{
 const api=vi.fn(async(path:string,method='GET')=>path.endsWith('/health-monitors')&&method==='GET'?[]:[]);
 render(<HealthPanel api={api} org="fixture" canManage={true} assets={[{id:'asset1',origin:'https://example.test',verified:true}]}/>);
 expect(await screen.findByText('No monitoring set up yet')).toBeTruthy();
 const user=userEvent.setup();
 await user.click(screen.getByRole('button',{name:'Add a monitor'}));
 expect(screen.getByText('Create an approved monitor')).toBeTruthy();
 const submit=screen.getByRole('button',{name:'Authorize monitoring'});
 expect(submit).toHaveProperty('disabled',true);
 await user.selectOptions(screen.getByLabelText('Verified website'),'asset1');
 expect(submit).toHaveProperty('disabled',true);
 expect(api.mock.calls.filter(x=>x[1]==='PUT')).toHaveLength(0);
});

it('groups advanced security and business tools while preserving navigation',async()=>{
 const onNavigate=vi.fn();const user=userEvent.setup();
 render(<WorkspaceNavigation page="Overview" onNavigate={onNavigate}/>);
 await user.click(screen.getByRole('button',{name:/Tools & settings/}));
 expect(screen.getByRole('button',{name:'Security tools'})).toBeTruthy();
 expect(screen.getByRole('button',{name:'Workspace & support'})).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Workspace & support'}));
 await user.click(screen.getByRole('button',{name:'Account security'}));
 expect(onNavigate).toHaveBeenCalledWith('Account security');
});
it('explains advanced tools with useful navigation and no implied automatic action',async()=>{
 const onNavigate=vi.fn();const user=userEvent.setup();
 render(<WorkspaceToolGuide page="API Assessment" onNavigate={onNavigate}/>);
 expect(screen.getByText(/Choose a verified origin/)).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'My websites'}));
 expect(onNavigate).toHaveBeenCalledWith('Assets');
});
