import React from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ContactExperience,{AEGIS_CONTACT_EMAIL} from '../app/contact/ContactExperience';
import Landing from '../app/page';

vi.mock('../app/Shield',()=>({default:()=> <div data-testid="hero-shield"/>}));
afterEach(()=>{cleanup();localStorage.removeItem('aegis-language');vi.unstubAllGlobals()});

it('publishes the actual AEGIS contact email with direct mailto and safe support advice',()=>{
 const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);
 render(<ContactExperience/>);
 expect(AEGIS_CONTACT_EMAIL).toBe('aegis.pentest@gmail.com');
 const address=screen.getByRole('link',{name:AEGIS_CONTACT_EMAIL}) as HTMLAnchorElement;
 expect(address.getAttribute('href')).toBe('mailto:aegis.pentest@gmail.com');
 expect(screen.getByRole('link',{name:/Write an email/}).getAttribute('href')).toContain('mailto:aegis.pentest@gmail.com');
 expect(screen.getByText(/never email passwords, one-time codes/)).toBeTruthy();
 expect(fetcher).not.toHaveBeenCalled();
});
it('allows visitors to read contact instructions in Arabic',async()=>{
 const user=userEvent.setup();
 render(<ContactExperience/>);
 await user.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));
 expect(screen.getByRole('heading',{name:'تواصل معنا بالبريد'})).toBeTruthy();
 expect(screen.getByRole('link',{name:'aegis.pentest@gmail.com'})).toBeTruthy();
 expect(screen.getByRole('link',{name:/ابعت رسالة/}).getAttribute('href')).toContain('mailto:');
});
it('exposes contact in the public landing navigation and footer',()=>{
 render(<Landing/>);
 expect(screen.getAllByRole('link',{name:/Contact Us/}).length).toBeGreaterThan(1);
 expect(screen.getByText(/Email aegis.pentest@gmail.com/)).toBeTruthy();
});
