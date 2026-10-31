import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,expect,it,vi} from 'vitest';
import GuidesExplorer from '../app/guides/GuidesExplorer';

afterEach(()=>{cleanup();localStorage.removeItem('aegis-language');vi.unstubAllGlobals()});

it('shows all public verification tutorials and plays steps without login or API traffic',async()=>{
 localStorage.removeItem('aegis-language');
 const requests=vi.fn();
 vi.stubGlobal('fetch',requests);
 render(<GuidesExplorer/>);
 const user=userEvent.setup();
 expect(screen.getByRole('heading',{name:/Verify your website/})).toBeTruthy();
 expect(screen.getByText(/No account required to watch/)).toBeTruthy();
 expect(screen.getByRole('button',{name:'Shopify'})).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Shopify'}));
 expect(screen.getByText(/published theme in your Shopify Online Store/)).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Verification method'}));
 expect(screen.getByText('Verify with an HTML meta tag')).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Next'}));
 expect(screen.getByText(/Paste it in the public homepage HTML head/)).toBeTruthy();
 expect(requests).not.toHaveBeenCalled();
 expect(screen.getAllByRole('link').some(link=>link.getAttribute('href')==='/console')).toBe(true);
});

it('makes independent HTML, DNS and meta walkthroughs accessible',async()=>{
 localStorage.removeItem('aegis-language');
 render(<GuidesExplorer/>);
 const user=userEvent.setup();
 for(const [name,title] of [
  ['HTML verification file','Verify with an HTML file'],
  ['DNS TXT record','Verify with a DNS TXT record'],
  ['HTML meta tag','Verify with an HTML meta tag'],
 ]){
  await user.click(screen.getByRole('button',{name}));
  await user.click(screen.getByRole('button',{name:'Verification method'}));
  expect(screen.getByText(title)).toBeTruthy();
 }
});
