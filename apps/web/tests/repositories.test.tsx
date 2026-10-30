import React from 'react';
import {render,screen,cleanup,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import RepositoryPanel from '../app/console/RepositoryPanel';
afterEach(cleanup);
const patch={id:'p',repository:'owned/site',diff:'+ nosniff',status:'review_required',tests:{application_tests:'not run'},pull_number:null};
const api=()=>vi.fn(async(path:string)=>path.endsWith('/repository-patches')?[patch]:path.includes('/repositories?')?[{name:'owned/site'}]:path.endsWith('/github')?[{id:'c',login:'owner',expires:9999999999,revoked:false}]:{});
it('viewer can inspect a diff but has no publish or connect controls',async()=>{
 render(<RepositoryPanel api={api()} org="o" requests={[]} role="viewer"/>);
 expect(screen.getByText('No repository proposals recorded.')).toBeTruthy();
 expect(screen.queryByText('Connect GitHub App')).toBeNull();
 expect(screen.queryByText('Publish approved draft PR')).toBeNull();
});
it('publishing requires exact diff approval and MFA input',async()=>{
 const call=api();render(<RepositoryPanel api={call} org="o" requests={[]} role="owner"/>);
 const button=await screen.findByRole('button',{name:'Publish approved draft PR'}) as HTMLButtonElement;
 expect(button.disabled).toBe(true);
 const user=userEvent.setup();await user.click(screen.getByLabelText(/I reviewed this exact diff/));
 expect(button.disabled).toBe(true);
 await user.type(screen.getByLabelText('Authenticator or recovery code'),'123456');await user.click(button);
 await waitFor(()=>expect(call).toHaveBeenCalledWith('/repository-patches/p/pull-request','POST',{accepted:true,mfa_code:'123456'}));
});
it('changing repository selection clears prior analysis consent',async()=>{
 render(<RepositoryPanel api={api()} org="o" requests={[{id:'r',finding_title:'MIME protection'}]} role="owner"/>);
 const user=userEvent.setup();await screen.findByText('+ nosniff');
 await user.click(screen.getByLabelText(/I authorize this workspace/));
 await user.selectOptions(screen.getByLabelText('GitHub connection'),'c');
 expect((screen.getByLabelText(/I authorize this workspace/) as HTMLInputElement).checked).toBe(false);
});

it('loads the explicitly selected repository page',async()=>{
 const call=api();render(<RepositoryPanel api={call} org="o" requests={[]} role="owner"/>);
 await screen.findByText('+ nosniff');const user=userEvent.setup();
 await user.selectOptions(screen.getByLabelText('GitHub connection'),'c');
 await user.click(screen.getByText('Next repository page'));
 await user.click(screen.getByText('Load authorized repositories'));
 await waitFor(()=>expect(call).toHaveBeenCalledWith('/github/connections/c/repositories?page=2'));
});

it('changing the configuration adapter clears consent',async()=>{
 render(<RepositoryPanel api={api()} org="o" requests={[]} role="owner"/>);
 const user=userEvent.setup();await screen.findByText('+ nosniff');
 await user.click(screen.getByLabelText(/I authorize this workspace/));
 await user.selectOptions(screen.getByLabelText('Configuration platform'),'netlify');
 expect((screen.getByLabelText(/I authorize this workspace/) as HTMLInputElement).checked).toBe(false);
 expect(screen.getByText(/Netlify support covers static responses only/)).toBeTruthy();
});
