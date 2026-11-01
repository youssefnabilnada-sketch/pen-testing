import React from 'react';
import {render,screen,cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,it,expect,vi} from 'vitest';
import AboutExperience from '../app/about/AboutExperience';
import Landing from '../app/page';

afterEach(()=>{cleanup();localStorage.removeItem('aegis-language');vi.unstubAllGlobals()});

it('explains AEGIS mission, vision and limited authorized capabilities publicly without any API calls',()=>{
 const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);
 render(<AboutExperience/>);
 expect(screen.getByRole('heading',{name:'Make security easier to act on.'})).toBeTruthy();
 expect(screen.getByRole('heading',{name:'A clearer, more responsible digital future.'})).toBeTruthy();
 expect(screen.getByRole('heading',{name:'What AEGIS does not promise'})).toBeTruthy();
 expect(screen.getByText(/not a comprehensive penetration test/i)).toBeTruthy();
 expect(screen.getByText(/does not automatically repair every vulnerability/i)).toBeTruthy();
 expect(screen.getByRole('link',{name:/Create your workspace/}).getAttribute('href')).toBe('/console');
 expect(fetcher).not.toHaveBeenCalled();
});

it('switches the public about page to Arabic and keeps navigation accessible',async()=>{
 const user=userEvent.setup();
 render(<AboutExperience/>);
 await user.click(screen.getByRole('button',{name:'التبديل إلى العربية'}));
 expect(screen.getByRole('heading',{name:'نحوّل فهم الأمان إلى خطوات عملية.'})).toBeTruthy();
 expect(screen.getByRole('heading',{name:'مستقبل رقمي أوضح وأكثر مسؤولية.'})).toBeTruthy();
 expect(screen.getByRole('heading',{name:'ما الذي لا تعدك به AEGIS؟'})).toBeTruthy();
 expect(document.querySelector('main.about-landing')?.getAttribute('dir')).toBe('rtl');
 expect(localStorage.getItem('aegis-language')).toBe('ar');
 await user.click(screen.getByRole('button',{name:'Switch to English'}));
 expect(screen.getByRole('heading',{name:'Make security easier to act on.'})).toBeTruthy();
});

it('links the existing landing page to About and exposes mission and vision before signup',()=>{
 render(<Landing/>);
 expect(screen.getByRole('link',{name:'About AEGIS'}).getAttribute('href')).toBe('/about');
 expect(screen.getByRole('heading',{name:'Our mission'})).toBeTruthy();
 expect(screen.getByRole('heading',{name:'Our vision'})).toBeTruthy();
 expect(screen.getByRole('link',{name:/Discover our story/}).getAttribute('href')).toBe('/about');
});
