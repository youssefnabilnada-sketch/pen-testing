import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import VerificationRecommendation from '../app/console/VerificationRecommendation';
afterEach(cleanup);
it.each([
 ['cloudflare','dns'],['vercel','file'],['netlify','file'],['wordpress','meta'],
 ['cpanel','file'],['plesk','file'],['github','file'],['custom','file'],
 ['shopify','meta'],['wix','meta'],['squarespace','dns'],['google','dns']
])('recommends an actual AEGIS proof method for %s',async(platform,method)=>{
 const choose=vi.fn();render(<VerificationRecommendation onChoose={choose}/>);const user=userEvent.setup();
 await user.selectOptions(screen.getByLabelText('Website platform or hosting'),platform);
 await user.click(screen.getByRole('button',{name:'Use recommended method'}));
 expect(choose).toHaveBeenCalledWith(method);
 expect(screen.getByText(/optional, explicitly authorized TXT-only Cloudflare publishing/)).toBeTruthy();
});
it('lets people choose a popular provider without requiring GitHub',async()=>{
 const onChoose=vi.fn();render(<VerificationRecommendation onChoose={onChoose}/>);const user=userEvent.setup();
 await user.click(screen.getByRole('button',{name:'Shopify'}));
 expect(screen.getByText('Add a tag to your store theme')).toBeTruthy();
 await user.click(screen.getByRole('button',{name:'Use recommended method'}));
 expect(onChoose).toHaveBeenCalledWith('meta');
});
it('does not imply that Google login alone confirms ownership',async()=>{
 render(<VerificationRecommendation onChoose={vi.fn()}/>);
 await userEvent.click(screen.getByRole('button',{name:'Google Search Console'}));
 expect(screen.getByText('Direct Google authorization is not connected yet. No Google password or token is requested.')).toBeTruthy();
 expect(screen.getByText(/Google Search Console ownership does not automatically prove ownership/)).toBeTruthy();
});
it('provides Arabic guidance with right-to-left direction',async()=>{
 render(<VerificationRecommendation onChoose={vi.fn()}/>);
 await userEvent.click(screen.getByRole('button',{name:'العربية'}));
 expect(screen.getByRole('region',{name:'Verification recommendation'}).getAttribute('dir')).toBe('rtl');
 expect(screen.getByText('استخدام هذه الطريقة')).toBeTruthy();
});
