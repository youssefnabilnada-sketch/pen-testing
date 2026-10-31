import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect} from 'vitest';
import SmartVerifyVideoGuide from '../app/console/SmartVerifyVideoGuide';

afterEach(cleanup);

it('provides a self-contained visual walkthrough for Shopify and actual meta proof',async()=>{
 const user=userEvent.setup();
 render(<SmartVerifyVideoGuide platform="shopify" method="meta"/>);
 const button=screen.getByRole('button',{name:'Watch animated guide'});
 expect(button.getAttribute('aria-expanded')).toBe('false');
 await user.click(button);
 expect(screen.getByText(/published theme in your Shopify Online Store/)).toBeTruthy();
 expect(screen.getByRole('button',{name:'Pause'})).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Verification method'}));
 expect(screen.getByText('Verify with an HTML meta tag')).toBeTruthy();
 expect(screen.getByText('Copy the unique meta tag from AEGIS.')).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Next'}));
 expect(screen.getByText(/Paste it in the public homepage HTML head/)).toBeTruthy();
 expect(screen.getByText(/not a recording of a live provider account/)).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Hide lesson'}));
 expect(screen.queryByRole('button',{name:'Play'})).toBeNull();
});

it('supports file, DNS, and HTML proof walkthroughs without contacting the API',async()=>{
 const user=userEvent.setup();
 for(const [method,label] of [['file','Verify with an HTML file'],['dns','Verify with a DNS TXT record'],['meta','Verify with an HTML meta tag']]){
  const view=render(<SmartVerifyVideoGuide platform="unsure" method={method}/>);
  await user.click(screen.getByRole('button',{name:'Watch animated guide'}));
  await user.click(screen.getByRole('button',{name:'Verification method'}));
  expect(screen.getByText(label)).toBeTruthy();
  expect(screen.getByText(/Only the real AEGIS verification check confirms ownership/)).toBeTruthy();
  view.unmount();
 }
});
