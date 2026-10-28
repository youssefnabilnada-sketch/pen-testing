import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,expect,it,vi} from 'vitest';
import OwnershipGuide from '../app/console/OwnershipGuide';

afterEach(cleanup);
it('previews a single Cloudflare TXT proof and requires explicit approval before sending the token',async()=>{
 const proof={id:'challenge-test',method:'dns',token:'owned-proof',instruction:'_aegis.example.test TXT aegis=owned-proof',expires:4102444800};
 const calls: Array<{url:string;data:unknown}> = [];
 const api=vi.fn(async(url:string,method?:string,data?:unknown)=>{
   calls.push({url,data});
   if(url.endsWith('/verification-recommendation'))return {method:'dns',reason:'DNS supported',source:'selected'};
   if(url.endsWith('/challenge'))return proof;
   if(url.endsWith('/cloudflare/preview'))return {name:'_aegis.example.test',content:'aegis=owned-proof',ttl:300};
   if(url.endsWith('/cloudflare/publish'))return {published:true,message:'TXT proof published.'};
   if(url.endsWith('/verification-history'))return [];
   return {};
 });
 const user=userEvent.setup();
 render(<OwnershipGuide assetId="asset1" api={api} onVerified={async()=>{}} />);
 const cloudflare=await screen.findByText(/Publish this TXT proof using Cloudflare/);
 await user.click(cloudflare);
 // The publish controls must remain hidden until the customer reviews the exact DNS change.
 expect(screen.queryByRole('button',{name:'Publish this single TXT record'})).toBeNull();
 expect(calls.filter(c=>c.url.endsWith('/cloudflare/publish'))).toHaveLength(0);
 await user.click(screen.getByRole('button',{name:'Review exact DNS change'}));
 expect(await screen.findByText(/Record: _aegis.example.test/)).toBeTruthy();
 const publish=screen.getByRole('button',{name:'Publish this single TXT record'});
 expect((publish as HTMLButtonElement).disabled).toBe(true);
 await user.type(screen.getByLabelText('Cloudflare zone ID'),'f'.repeat(32));
 await user.type(screen.getByLabelText('Scoped Cloudflare API token'),'temporary-token-for-my-zone');
 expect((publish as HTMLButtonElement).disabled).toBe(true);
 await user.click(screen.getByLabelText(/I authorize creating this exact TXT record/));
 expect((publish as HTMLButtonElement).disabled).toBe(false);
 await user.click(publish);
 const posts=calls.filter(c=>c.url.endsWith('/cloudflare/publish'));
 expect(posts).toHaveLength(1);
 expect(posts[0].data).toEqual({zone_id:'f'.repeat(32),api_token:'temporary-token-for-my-zone',confirm_dns_change:true,mfa_code:''});
 expect((screen.getByLabelText('Scoped Cloudflare API token') as HTMLInputElement).value).toBe('');
});
