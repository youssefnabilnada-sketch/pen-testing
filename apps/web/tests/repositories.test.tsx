import React from 'react';
import {render,screen,cleanup,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import RepositoryPanel from '../app/console/RepositoryPanel';
afterEach(cleanup);
const patch={id:'p',repository:'owned/site',diff:'+ nosniff',status:'review_required',tests:{application_tests:'not run'},pull_number:null};
const api=()=>vi.fn(async(path:string)=>path.endsWith('/repository-patches')?[patch]:path.includes('/repositories?')?[{name:'owned/site'}]:path.endsWith('/github')?[{id:'c',login:'owner',expires:9999999999,revoked:false}]:{});
it('viewer can inspect public explanation but cannot connect or publish patches',async()=>{
 render(<RepositoryPanel api={api()} org="o" requests={[]} role="viewer"/>);
 expect(screen.getByText('No code proposals yet')).toBeTruthy();
 expect(screen.queryByRole('button',{name:'Connect GitHub securely'})).toBeNull();
 expect(screen.queryByRole('button',{name:'Publish approved draft PR'})).toBeNull();
});
it('publishing an existing proposal requires explicit exact diff review and MFA',async()=>{
 const call=api();render(<RepositoryPanel api={call} org="o" requests={[]} role="owner"/>);
 const button=await screen.findByRole('button',{name:'Publish approved draft PR'}) as HTMLButtonElement;
 expect(button.disabled).toBe(true);
 const user=userEvent.setup();await user.click(screen.getByLabelText(/I reviewed this exact diff/));
 expect(button.disabled).toBe(true);
 await user.type(screen.getByLabelText('Authenticator or recovery code'),'123456');await user.click(button);
 await waitFor(()=>expect(call).toHaveBeenCalledWith('/repository-patches/p/pull-request','POST',{accepted:true,mfa_code:'123456'}));
});
it('changing the connected account clears previous GitHub connection consent',async()=>{
 render(<RepositoryPanel api={api()} org="o" requests={[{id:'r',finding_title:'MIME protection'}]} role="owner"/>);
 const user=userEvent.setup();await screen.findByText('Review exact code diff and tests');
 const consent=screen.getByRole('checkbox',{name:/I authorize AEGIS to request access/}) as HTMLInputElement;
 await user.click(consent);
 await user.selectOptions(screen.getByLabelText('Connected account'),'c');
 await waitFor(()=>expect(consent.checked).toBe(false));
});
it('loads authorized repositories only for the selected connection and page',async()=>{
 const call=api();render(<RepositoryPanel api={call} org="o" requests={[]} role="owner"/>);
 const user=userEvent.setup();await screen.findByText('Review exact code diff and tests');
 await user.selectOptions(screen.getByLabelText('Connected account'),'c');
 await waitFor(()=>expect(call).toHaveBeenCalledWith('/github/connections/c/repositories?page=1'));
 await screen.findByRole('option',{name:'owned/site'});
 await user.click(screen.getByRole('button',{name:'Next'}));
 await waitFor(()=>expect(call).toHaveBeenCalledWith('/github/connections/c/repositories?page=2'));
});
it('changing platform resets repository-specific proposal authorization',async()=>{
 render(<RepositoryPanel api={api()} org="o" requests={[{id:'r',finding_title:'MIME protection'}]} role="owner"/>);
 const user=userEvent.setup();await screen.findByText('Review exact code diff and tests');
 await user.selectOptions(screen.getByLabelText('Connected account'),'c');
 await screen.findByRole('option',{name:'owned/site'});
 await user.selectOptions(screen.getByLabelText('Repository'),'owned/site');
 await user.selectOptions(screen.getByLabelText('Finding with a remediation request'),'r');
 const consent=screen.getByRole('checkbox',{name:/I authorize this specific repository and finding/}) as HTMLInputElement;
 await user.click(consent);
 expect(consent.checked).toBe(true);
 await user.selectOptions(screen.getByLabelText('Hosting platform'),'netlify');
 await waitFor(()=>expect(consent.checked).toBe(false));
 expect(screen.getByText(/Only the supported hosting configuration changes/)).toBeTruthy();
});
