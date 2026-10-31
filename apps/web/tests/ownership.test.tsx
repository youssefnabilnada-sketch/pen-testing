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
 await user.type(screen.getByLabelText('GitHub repository link (or owner/name)'),'owner/site');
 await user.click(screen.getByRole('button',{name:'Prepare file on GitHub'}));
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

it('guides an owned GitHub website without auto-authorizing an assessment',async()=>{
 const posts: Array<{path:string;method:string|undefined;data:unknown}>=[];
 const challenge={id:'proof-fixture',method:'file',token:'approved-proof-token',instruction:'https://owned.example.test/.well-known/aegis-approved-proof-token.txt',expires:4102444800};
 const api=vi.fn(async(path:string,method?:string,data?:unknown)=>{
  if(method==='POST')posts.push({path,method,data});
  if(path.endsWith('/challenge')&&method!=='POST')return null;
  if(path.endsWith('/challenge')&&method==='POST')return challenge;
  if(path.endsWith('/github'))return {url:'https://github.com/owner/site/new/main?filename=proof'};
  return {};
 });
 const user=userEvent.setup();
 render(<OwnershipGuide assetId="owned-asset" api={api} onVerified={vi.fn(async()=>{})}/>);
 const github=screen.getByRole('button',{name:'GitHub / GitHub Pages'});
 await user.click(github);
 expect(github.getAttribute('aria-pressed')).toBe('true');
 expect(posts).toHaveLength(0);
 await user.click(screen.getByRole('button',{name:'Get verification instructions'}));
 expect(posts[0]).toMatchObject({path:'/assets/owned-asset/challenge',data:{method:'file'}});
 await user.type(screen.getByLabelText('GitHub repository link (or owner/name)'),'https://github.com/owner/site');
 await user.click(screen.getByRole('button',{name:'Prepare file on GitHub'}));
 expect(posts[1]).toMatchObject({path:'/assets/owned-asset/challenge/proof-fixture/github',
  data:{repository:'owner/site',branch:'main',directory:''}});
 expect(await screen.findByRole('link',{name:/Open prepared file on GitHub/})).toBeTruthy();
 expect(posts.some(x=>x.path.includes('/assessments')||x.path.includes('/authorize'))).toBe(false);
});

it('guides a Shopify owner to a real meta proof without any scan or account connector',async()=>{
 const calls:Array<[string,string|undefined,unknown]>=[];
 const api=vi.fn(async(path:string,method?:string,data?:unknown)=>{
  calls.push([path,method,data]);
  if(path.endsWith('/challenge')&&method==='GET')return null;
  if(path.endsWith('/challenge')&&method==='POST')return {id:'proof',method:(data as {method:string}).method,token:'token',instruction:'Exact meta tag',expires:4102444800};
  return null;
 });
 const done=vi.fn(async()=>{});render(<OwnershipGuide assetId="owned" api={api} onVerified={done}/>);
 const user=userEvent.setup();
 await user.click(screen.getByRole('button',{name:'Shopify'}));
 expect(screen.getByText(/published theme in your Shopify Online Store/)).toBeTruthy();
 expect(calls.filter(([path,method])=>method==='POST')).toHaveLength(0);
 await user.click(screen.getByRole('button',{name:/Get verification instructions/}));
 expect(await screen.findByText('Exact meta tag')).toBeTruthy();
 expect(calls).toContainEqual(['/assets/owned/challenge','POST',{method:'meta'}]);
 expect(calls.every(([path])=>!path.includes('/assessments')&&!path.includes('/authorize'))).toBe(true);
 expect(done).not.toHaveBeenCalled();
});
it('offers Wix, Squarespace and Google without claiming unsupported direct Google ownership',async()=>{
 const api=vi.fn(async(_path:string,_method?:string)=>null);
 render(<OwnershipGuide assetId="a" api={api} onVerified={vi.fn()}/>);
 const user=userEvent.setup();
 await user.click(screen.getByText('More options: Wix, Squarespace and Google Search Console'));
 const google=screen.getByRole('button',{name:'Google Search Console'});
 await user.click(google);
 expect(google.getAttribute('aria-pressed')).toBe('true');
 expect(screen.getByText(/Direct Google Search Console authorization is not connected yet/)).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Wix'}));
 expect(screen.getByText(/DNS proof requires control of the domain/)).toBeTruthy();
 expect(api.mock.calls.some(([path,method])=>method==='POST'||path.includes('/verify/'))).toBe(false);
});
