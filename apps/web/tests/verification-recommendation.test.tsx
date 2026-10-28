import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import VerificationRecommendation from '../app/console/VerificationRecommendation';
afterEach(cleanup);
it.each([['cloudflare','dns'],['vercel','file'],['netlify','file'],['wordpress','meta'],['cpanel','file'],['plesk','file'],['github','file'],['other','dns']])('recommends a supported manual method for %s',async(platform,method)=>{
 const choose=vi.fn();render(<VerificationRecommendation onChoose={choose}/>);const user=userEvent.setup();
 await user.selectOptions(screen.getByLabelText('Website platform or hosting'),platform);
 await user.click(screen.getByRole('button',{name:'Use recommended method'}));expect(choose).toHaveBeenCalledWith(method);
 expect(screen.getByText(/optional, explicitly authorized TXT-only Cloudflare publishing/)).toBeTruthy();
});
it('provides Arabic guidance with right-to-left direction',async()=>{
 render(<VerificationRecommendation onChoose={vi.fn()}/>);await userEvent.click(screen.getByRole('button',{name:'العربية'}));
 expect(screen.getByRole('region',{name:'Verification recommendation'}).getAttribute('dir')).toBe('rtl');
 expect(screen.getByText('استخدام هذه الطريقة')).toBeTruthy();
});
